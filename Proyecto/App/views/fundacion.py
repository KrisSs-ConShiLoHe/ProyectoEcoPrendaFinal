from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.utils import timezone
from django.http import JsonResponse
from django import forms  # Agregado para forms
import hashlib
import json
import logging  # Agregado para logging

from ..models import (
    Usuario, Prenda, Transaccion, TipoTransaccion, 
    Fundacion, Mensaje, ImpactoAmbiental, 
    Logro, UsuarioLogro, CampanaFundacion
)
from ..decorators import (
    login_required_custom, 
    anonymous_required,
    ajax_login_required, 
    session_valid,
    admin_required,
    representante_fundacion_required,
    moderador_required,
    cliente_only,
    role_required,
)

from django.conf import settings

from ..forms import RegistroForm, PerfilForm, PrendaForm
from .auth import get_usuario_actual

# Configuración de logging
logger = logging.getLogger(__name__)

def lista_fundaciones(request):
    """Lista todas las fundaciones registradas."""
    usuario = get_usuario_actual(request)
    fundaciones = Fundacion.objects.filter(activa=True)
    context = {
        'usuario': usuario,
        'fundaciones': fundaciones,
    }
    return render(request, 'fundaciones/lista_fundaciones.html', context)

def detalle_fundacion(request, id_fundacion):
    """Muestra información y estadísticas de una fundación."""
    usuario = get_usuario_actual(request)
    fundacion = get_object_or_404(Fundacion.objects.select_related('representante'), pk=id_fundacion)  # Cambiado: 'pk=id_fundacion', agregado select_related
    # Donaciones recibidas por la fundación, ordenadas por más recientes
    donaciones = Transaccion.objects.filter(
        fundacion=fundacion,  # Cambiado: 'fundacion'
        tipo__nombre_tipo='Donación'  # Cambiado: 'tipo__nombre_tipo'
    ).select_related('prenda', 'user_origen').order_by('-fecha_transaccion')  # Cambiado: 'prenda', 'user_origen', agregado select_related

    # Impacto ambiental total de todas las prendas donadas a esta fundación
    prendas_donadas = [don.prenda for don in donaciones if don.prenda]  # Cambiado: 'don.prenda'
    impacto_total = ImpactoAmbiental.objects.filter(
        prenda__in=prendas_donadas  # Cambiado: 'prenda__in'
    ).aggregate(
        total_carbono=Sum('carbono_evitar_kg'),
        total_energia=Sum('energia_ahorrada_kwh')
    )

    # Verificar si el usuario es representante de esta fundación
    puede_editar = usuario.es_representante_fundacion() and usuario.fundacion_asignada == fundacion

    context = {
        'usuario': usuario,
        'fundacion': fundacion,
        'donaciones': donaciones,
        'impacto_total': impacto_total,
        'puede_editar': puede_editar,
    }
    return render(request, 'fundaciones/detalle_fundacion.html', context)

@representante_fundacion_required
def panel_fundacion(request):
    """Dashboard de la fundación del usuario: campañas, donaciones, estadísticas."""
    usuario = get_usuario_actual(request)
    fundacion = usuario.fundacion_asignada
    
    # Obtener donaciones recibidas
    donaciones_recibidas = Transaccion.objects.filter(
        fundacion=fundacion,
        tipo__nombre_tipo='Donación'
    ).select_related('prenda', 'user_origen')
    
    # Calcular impacto ambiental desde las prendas donadas
    impacto = ImpactoAmbiental.objects.filter(
        prenda__transaccion__fundacion=fundacion,
        prenda__transaccion__tipo__nombre_tipo='Donación'
    ).aggregate(
        total_carbono=Sum('carbono_evitar_kg'),
        total_energia=Sum('energia_ahorrada_kwh'),
    )
    
    # Obtener campañas de la fundación
    campanas = CampanaFundacion.objects.filter(fundacion=fundacion).order_by('-fecha_inicio')
    
    # Estadísticas generales
    total_donaciones = donaciones_recibidas.count()
    donaciones_pendientes = donaciones_recibidas.filter(estado='PENDIENTE').count()
    donaciones_completadas = donaciones_recibidas.filter(estado='COMPLETADA').count()
    
    context = {
        'usuario': usuario,
        'fundacion': fundacion,
        'donaciones_recibidas': donaciones_recibidas[:10],  # Últimas 10
        'total_donaciones': total_donaciones,
        'donaciones_pendientes': donaciones_pendientes,
        'donaciones_completadas': donaciones_completadas,
        'impacto': impacto,
        'campanas': campanas,
    }
    return render(request, 'fundaciones/panel_fundacion.html', context)

@representante_fundacion_required
def gestionar_donaciones(request):
    """Lista todas las donaciones a la fundación, permite confirmar o rechazar."""
    usuario = get_usuario_actual(request)
    fundacion = usuario.fundacion_asignada
    donaciones = Transaccion.objects.filter(fundacion=fundacion, tipo__nombre_tipo='Donación', estado='PENDIENTE')
    context = {
        'usuario': usuario,
        'fundacion': fundacion,
        'donaciones': donaciones,
    }
    return render(request, 'fundaciones/gestionar_donaciones.html', context)

@representante_fundacion_required
def confirmar_recepcion_donacion(request, id_transaccion):
    """Confirma la recepción de una donación y actualiza estados."""
    usuario = get_usuario_actual(request)
    transaccion = get_object_or_404(
        Transaccion,
        pk=id_transaccion,
        fundacion=usuario.fundacion_asignada
    )

    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido. Debes confirmar mediante POST.'}, status=405)

    if transaccion.estado != 'EN_PROCESO':
        return JsonResponse({'error': 'La donación aún no ha sido marcada como entregada por el donante.'}, status=400)

    transaccion.estado = 'COMPLETADA'
    transaccion.fecha_entrega = timezone.now()
    transaccion.save()
    transaccion.actualizar_disponibilidad_prenda()

    Mensaje.objects.create(
        emisor=usuario,
        receptor=transaccion.user_origen,
        contenido=f"Gracias por tu donación de {transaccion.prenda.nombre}! Tu prenda ha sido recibida y será destinada a {transaccion.fundacion.nombre}.",
        fecha_envio=timezone.now()
    )

    verificar_logros(transaccion.user_origen)
    messages.success(request, 'Donación confirmada y donante notificado.')
    return redirect('gestionar_donaciones')

@representante_fundacion_required
def enviar_mensaje_agradecimiento(request, id_usuario_donante):
    """Envía un mensaje personalizado de agradecimiento al donante."""
    usuario = get_usuario_actual(request)
    donante = get_object_or_404(Usuario, id_usuario=id_usuario_donante)
    if request.method == 'POST':
        contenido = request.POST.get('contenido')
        if not contenido:
            messages.error(request, 'Escribe un mensaje de agradecimiento.')
        else:
            Mensaje.objects.create(
                emisor=usuario,
                receptor=donante,
                contenido=contenido,
                fecha_envio=timezone.now()
            )
            messages.success(request, f'Mensaje enviado a {donante.nombre}.')
            return redirect('panel_fundacion')
    context = {
        'usuario': usuario,
        'donante': donante,
    }
    return render(request, 'mensajes/enviar_mensaje_agradecimiento.html', context)

@representante_fundacion_required
def estadisticas_donaciones(request):
    """Panel con estadísticas avanzadas de donaciones de la fundación."""
    usuario = get_usuario_actual(request)
    fundacion = usuario.fundacion_asignada
    donaciones = Transaccion.objects.filter(fundacion=fundacion, tipo__nombre_tipo='Donación', prenda__isnull=False).select_related('prenda', 'user_origen')
    resumen = donaciones.values('estado').annotate(total=Count('id'))
    prendas = Prenda.objects.filter(pk__in=Transaccion.objects.filter(fundacion=fundacion, prenda__isnull=False).values_list('prenda_id', flat=True))
    context = {
        'fundacion': fundacion,
        'donaciones': donaciones,
        'resumen': list(resumen),
        'total_prendas': prendas.count()
    }
    return render(request, 'fundaciones/estadisticas_donaciones.html', context)

# ==============================================================================
# VISTA DEL MAPA INTERACTIVO
# ==============================================================================

def mapa_fundaciones(request):
    """
    Mapa interactivo que muestra:
    - Todas las fundaciones activas (SIEMPRE visibles)
    - Usuarios que han activado "mostrar_en_mapa" (OPCIONAL)
    
    Usa Geoapify + Leaflet.js para renderizar el mapa.
    """
    usuario = get_usuario_actual(request)
    
    # Obtener todas las fundaciones activas con coordenadas válidas
    fundaciones = Fundacion.objects.filter(
        activa=True,
        lat__isnull=False,
        lng__isnull=False
    ).values('id_fundacion', 'nombre', 'direccion', 'lat', 'lng', 'telefono', 'correo_contacto')

    # Obtener usuarios que aceptaron mostrar su ubicación
    usuarios_visibles = Usuario.objects.filter(
        mostrar_en_mapa=True,
        lat__isnull=False,
        lng__isnull=False
    ).values('id_usuario', 'nombre', 'comuna', 'lat', 'lng')
    
    # Convertir QuerySets a listas para JSON
    fundaciones_list = list(fundaciones)
    usuarios_list = list(usuarios_visibles)
    
    # Centro del mapa (Santiago, Chile por defecto)
    centro_lat = -33.4489
    centro_lng = -70.6693
    
    # Si hay fundaciones, centrar en la primera
    if fundaciones_list:
        centro_lat = fundaciones_list[0]['lat']
        centro_lng = fundaciones_list[0]['lng']
    
    context = {
        'usuario': usuario,
        'fundaciones_json': json.dumps(fundaciones_list),
        'usuarios_json': json.dumps(usuarios_list),
        'centro_lat': centro_lat,
        'centro_lng': centro_lng,
        'geoapify_api_key': settings.GEOAPIFY_API_KEY,
        'total_fundaciones': len(fundaciones_list),
        'total_usuarios_visibles': len(usuarios_list),
    }
    
    return render(request, 'fundaciones/mapa_fundaciones.html', context)


@login_required_custom
def actualizar_ubicacion_usuario(request):
    """
    Permite al usuario actualizar su ubicación en el mapa.
    Usa geocodificación de Geoapify para convertir dirección en coordenadas.
    """
    usuario = get_usuario_actual(request)
    
    if request.method == 'POST':
        direccion = request.POST.get('direccion')
        mostrar_en_mapa = request.POST.get('mostrar_en_mapa') == 'on'
        
        if not direccion:
            messages.error(request, 'Debes ingresar una dirección.')
            return redirect('perfil')
        
        # Geocodificar dirección usando Geoapify
        import requests
        
        geocode_url = f"https://api.geoapify.com/v1/geocode/search"
        params = {
            'text': direccion,
            'apiKey': settings.GEOAPIFY_API_KEY,
            'limit': 1
        }
        
        try:
            response = requests.get(geocode_url, params=params)
            data = response.json()
            
            if data.get('features') and len(data['features']) > 0:
                coords = data['features'][0]['geometry']['coordinates']
                lng, lat = coords[0], coords[1]
                
                # Actualizar usuario
                usuario.direccion = direccion
                usuario.lat = lat
                usuario.lng = lng
                usuario.mostrar_en_mapa = mostrar_en_mapa
                usuario.save()
                
                messages.success(request, f'Ubicación actualizada: {direccion}')
            else:
                messages.error(request, 'No se pudo encontrar la dirección. Intenta con una más específica.')
        
        except Exception as e:
            messages.error(request, f'Error al geocodificar: {str(e)}')
    
    return redirect('perfil')


@admin_required
def actualizar_ubicacion_fundacion(request, id_fundacion):
    """
    Permite a administradores actualizar la ubicación de una fundación.
    """
    fundacion = get_object_or_404(Fundacion, id_fundacion=id_fundacion)
    
    if request.method == 'POST':
        direccion = request.POST.get('direccion')
        
        if not direccion:
            messages.error(request, 'Debes ingresar una dirección.')
            return redirect('detalle_fundacion', id_fundacion=id_fundacion)
        
        # Geocodificar dirección
        import requests
        
        geocode_url = f"https://api.geoapify.com/v1/geocode/search"
        params = {
            'text': direccion,
            'apiKey': settings.GEOAPIFY_API_KEY,
            'limit': 1
        }
        
        try:
            response = requests.get(geocode_url, params=params)
            data = response.json()
            
            if data.get('features') and len(data['features']) > 0:
                coords = data['features'][0]['geometry']['coordinates']
                lng, lat = coords[0], coords[1]
                
                fundacion.direccion = direccion
                fundacion.lat = lat
                fundacion.lng = lng
                fundacion.save()
                
                messages.success(request, f'Ubicación de fundación actualizada: {direccion}')
            else:
                messages.error(request, 'No se pudo encontrar la dirección.')
        
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')

    return redirect('detalle_fundacion', id_fundacion=id_fundacion)

@representante_fundacion_required
def editar_fundacion(request):
    """Permite al representante editar la información de su fundación."""
    usuario = get_usuario_actual(request)
    fundacion = usuario.fundacion_asignada

    if request.method == 'POST':
        # Actualizar campos básicos
        fundacion.nombre = request.POST.get('nombre', fundacion.nombre)
        fundacion.correo_contacto = request.POST.get('correo_contacto', fundacion.correo_contacto)
        fundacion.telefono = request.POST.get('telefono', fundacion.telefono)
        fundacion.direccion = request.POST.get('direccion', fundacion.direccion)
        fundacion.descripcion = request.POST.get('descripcion', fundacion.descripcion)

        # Nuevos campos
        fundacion.beneficios_donacion = request.POST.get('beneficios_donacion', fundacion.beneficios_donacion)
        fundacion.responsabilidad_donante = request.POST.get('responsabilidad_donante', fundacion.responsabilidad_donante)

        # Manejar imagen del logo
        if 'imagen_fundacion' in request.FILES:
            fundacion.imagen_fundacion = request.FILES['imagen_fundacion']

        # Manejar imágenes adicionales (JSON field)
        imagenes_adicionales = fundacion.imagenes_adicionales or []
        if 'imagenes_adicionales' in request.FILES:
            for img in request.FILES.getlist('imagenes_adicionales'):
                # Aquí asumimos que subes a Cloudinary o similar, por ahora guardamos URLs dummy
                # En producción, integrar con Cloudinary
                imagenes_adicionales.append(f"/media/fundaciones/{img.name}")  # Placeholder
        fundacion.imagenes_adicionales = imagenes_adicionales

        fundacion.save()
        messages.success(request, 'Información de la fundación actualizada exitosamente.')
        return redirect('panel_fundacion')

    context = {
        'usuario': usuario,
        'fundacion': fundacion,
    }
    return render(request, 'fundaciones/editar_fundacion.html', context)
