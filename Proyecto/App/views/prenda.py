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

from ..cloudinary_utils import (
    subir_imagen_prenda,
    subir_imagen_usuario,
    subir_logo_fundacion,
    subir_imagen_campana,
    validar_imagen,
    eliminar_imagen_cloudinary,
    extraer_public_id_de_url,
    CloudinaryError
)

from ..carbon_utils import (
    calcular_impacto_prenda,
    calcular_impacto_transaccion,
    obtener_impacto_total_usuario,
    obtener_impacto_total_plataforma,
    generar_informe_impacto,
    formatear_equivalencia
)

from ..clarifai_utils import analizar_imagen_completa
from .auth import get_usuario_actual, obtener_permisos_usuario, es_propietario_prenda, puede_proponer_transaccion, puede_donar_prenda, puede_editar_prenda, puede_eliminar_prenda

# Configuración de logging
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------------------------------------------
# Gestión de Prendas 

@cliente_only
def lista_prendas(request):
    """Lista todas las prendas disponibles con opción de filtrado."""
    usuario = get_usuario_actual(request)
    prendas = Prenda.objects.filter(estado='DISPONIBLE').order_by('-fecha_publicacion')

    categoria = request.GET.get('categoria')
    talla = request.GET.get('talla')
    estado = request.GET.get('estado')

    if categoria:
        prendas = prendas.filter(categoria=categoria)
    if talla:
        prendas = prendas.filter(talla=talla)
    if estado:
        prendas = prendas.filter(estado=estado)

    # Enriquecer cada prenda con flags de permisos
    permisos = obtener_permisos_usuario(usuario)
    prendas_enriquecidas = []
    for prenda in prendas:
        prenda_data = {
            'prenda': prenda,
            'is_owner': es_propietario_prenda(usuario, prenda),
            'can_propose': puede_proponer_transaccion(usuario, prenda),
        }
        prendas_enriquecidas.append(prenda_data)

    context = {
        'usuario': usuario,
        'prendas': prendas_enriquecidas,
        'categorias': ['Camiseta', 'Pantalón', 'Vestido', 'Chaqueta', 'Zapatos', 'Accesorios'],
        'tallas': ['XS', 'S', 'M', 'L', 'XL', 'XXL'],
        'estados': ['Nuevo', 'Excelente', 'Bueno', 'Usado'],
        **permisos,
    }
    return render(request, 'prendas/lista_prendas.html', context)

@cliente_only
def detalle_prenda(request, id_prenda):
    """Detalle de prenda con impacto ambiental y equivalencias."""
    usuario = get_usuario_actual(request)
    prenda = get_object_or_404(Prenda, id_prenda=id_prenda)
    impacto_obj = ImpactoAmbiental.objects.filter(prenda=prenda).first()
    
    if impacto_obj:
        impacto = calcular_impacto_prenda(categoria=prenda.categoria, peso_kg=None)
    
    # Buscar transacción actual
    transaccion_actual = Transaccion.objects.filter(
        prenda=prenda,
        estado__in=['PENDIENTE', 'RESERVADA', 'EN_PROCESO']
    ).order_by('-fecha_transaccion').first()

    # Obtener permisos y flags
    permisos = obtener_permisos_usuario(usuario)
    is_owner = es_propietario_prenda(usuario, prenda)
    can_propose = puede_proponer_transaccion(usuario, prenda)
    can_donate = puede_donar_prenda(usuario, prenda)
    can_edit = puede_editar_prenda(usuario, prenda)
    can_delete = puede_eliminar_prenda(usuario, prenda)

    context = {
        'usuario': usuario,
        'prenda': prenda,
        'impacto': impacto_obj,
        'transaccion_actual': transaccion_actual,
        'is_owner': is_owner,
        'can_propose': can_propose,
        'can_donate': can_donate,
        'can_edit': can_edit,
        'can_delete': can_delete,
        **permisos,  # Añadir todos los permisos al contexto
    }
    return render(request, 'prendas/detalle_prenda.html', context)

@cliente_only
def crear_prenda(request):
    """Permite al cliente crear una nueva prenda con detección automática."""
    usuario = get_usuario_actual(request)
    
    if request.method == 'POST':
        imagen = request.FILES.get('imagen_prenda')
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')
        categoria = request.POST.get('categoria')
        talla = request.POST.get('talla')
        condicion = request.POST.get('estado')

        if not all([nombre, descripcion, categoria, talla, condicion]):
            messages.error(request, 'Todos los campos son obligatorios.')
            return render(request, 'crear_prenda.html', {
                'usuario': usuario,
                'categorias': ['Camiseta', 'Pantalón', 'Vestido', 'Chaqueta', 'Zapatos', 'Accesorios'],
                'tallas': ['XS', 'S', 'M', 'L', 'XL', 'XXL'],
                'estados': ['Nuevo', 'Excelente', 'Bueno', 'Usado'],
            })
        
        # Validar imagen si se proporciona
        if imagen:
            es_valida, mensaje_error = validar_imagen(imagen)
            if not es_valida:
                messages.error(request, mensaje_error)
                return redirect('crear_prenda')
        
        # Crear prenda
        prenda = Prenda.objects.create(
            user=usuario,
            nombre=nombre,
            descripcion=descripcion,
            categoria=categoria,
            talla=talla,
            estado='DISPONIBLE',
            fecha_publicacion=timezone.now()
        )
        
        # Subir imagen a Cloudinary si existe
        if imagen:
            try:
                resultado = subir_imagen_prenda(imagen, prenda.id_prenda)
                if resultado and resultado.get('secure_url'):
                    prenda.imagen_prenda = resultado['secure_url']
                    prenda.save()

                    # ✨ ANÁLISIS CON CLARIFAI ✨
                    try:
                        analisis = analizar_imagen_completa(imagen_url=resultado['secure_url'])

                        # Si la categoría sugerida es diferente, avisar al usuario
                        if analisis['categoria_sugerida'] and analisis['categoria_sugerida'] != categoria:
                            if analisis['confianza'] >= 0.7:
                                messages.warning(
                                    request,
                                    f"Clarifai detectó que podría ser '{analisis['categoria_sugerida']}' "
                                    f"con {analisis['confianza']*100:.0f}% de confianza. "
                                    f"Puedes editar la categoría si lo deseas."
                                )
                    except Exception as e:
                        print(f"Error al analizar con Clarifai: {e}")
                        # Continuar sin análisis
            except CloudinaryError as e:
                # Cloudinary no está configurado (desarrollo local) - usar URL local simulada
                try:
                    # Para desarrollo local, simular una URL de imagen
                    prenda.imagen_prenda = f"/media/prendas/{imagen.name}"
                    prenda.save()
                    logger.info(f"Imagen guardada localmente para prenda {prenda.id_prenda} (Cloudinary no disponible)")
                except Exception as local_error:
                    logger.warning(f"Error guardando imagen localmente: {str(local_error)}")
        
        # Calcular impacto ambiental
        impacto = calcular_impacto_prenda(categoria=categoria, peso_kg=None)
        
        # Guardar impacto en la base de datos
        ImpactoAmbiental.objects.create(
            prenda=prenda,
            carbono_evitar_kg=impacto['carbono_evitado_kg'],
            energia_ahorrada_kwh=impacto['energia_ahorrada_kwh'],
            fecha_calculo=timezone.now()
        )
        
        messages.success(
            request,
            f'¡Prenda publicada! Evitarás {impacto["carbono_evitado_kg"]} kg de CO₂ al reutilizarla.'
        )

        return redirect('detalle_prenda', id_prenda=prenda.id_prenda)

    context = {
        'usuario': usuario,
        'categorias': ['Camiseta', 'Pantalón', 'Vestido', 'Chaqueta', 'Zapatos', 'Accesorios'],
        'tallas': ['XS', 'S', 'M', 'L', 'XL', 'XXL'],
        'estados': ['Nuevo', 'Excelente', 'Bueno', 'Usado'],
    }
    return render(request, 'prendas/crear_prenda.html', context)

@cliente_only
def editar_prenda(request, id_prenda):
    """Permite al cliente editar una de sus prendas."""
    usuario = get_usuario_actual(request)
    prenda = get_object_or_404(Prenda, id_prenda=id_prenda)
    if prenda.user.id_usuario != usuario.id_usuario:
        messages.error(request, 'No tienes permiso para editar esta prenda.')
        return redirect('detalle_prenda', id_prenda=prenda.id_prenda)

    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')
        categoria = request.POST.get('categoria')
        talla = request.POST.get('talla')
        condicion = request.POST.get('estado')  # Renombrado a 'condicion' (es el estado de conservación, no de transacción)
        imagen = request.FILES.get('imagen_prenda')

        if not all([nombre, descripcion, categoria, talla, condicion]):
            messages.error(request, 'Todos los campos son obligatorios.')
            # Mantener campos en el formulario
        else:
            prenda.nombre = nombre
            prenda.descripcion = descripcion
            prenda.categoria = categoria
            prenda.talla = talla
            # NO modificar prenda.estado (se controla por transacciones, no por edición)
            if imagen:
                try:
                    resultado = subir_imagen_prenda(imagen, prenda.id_prenda)
                    if resultado and resultado.get('secure_url'):
                        prenda.imagen_prenda = resultado['secure_url']
                    else:
                        # Fallback para desarrollo local
                        prenda.imagen_prenda = f"/media/prendas/{imagen.name}"
                except CloudinaryError:
                    # Cloudinary no disponible, usar URL local
                    prenda.imagen_prenda = f"/media/prendas/{imagen.name}"
            prenda.save()
            messages.success(request, 'Prenda actualizada correctamente.')
            return redirect('detalle_prenda', id_prenda=prenda.id_prenda)

    context = {
        'usuario': usuario,
        'prenda': prenda,
        'categorias': ['Camiseta', 'Pantalón', 'Vestido', 'Chaqueta', 'Zapatos', 'Accesorios'],
        'tallas': ['XS', 'S', 'M', 'L', 'XL', 'XXL'],
        'estados': ['Nuevo', 'Excelente', 'Bueno', 'Usado'],
    }
    return render(request, 'prendas/editar_prenda.html', context)

@cliente_only
def eliminar_prenda(request, id_prenda):
    """Permite eliminar una prenda propia del usuario cliente."""
    usuario = get_usuario_actual(request)
    prenda = get_object_or_404(Prenda, id_prenda=id_prenda)
    if prenda.user.id_usuario != usuario.id_usuario:
        messages.error(request, 'No tienes permiso para eliminar esta prenda.')
        return redirect('detalle_prenda', id_prenda=prenda.id_prenda)
    if request.method == 'POST':
        # Elimina impacto y transacciones asociadas a la prenda
        prenda.impactoambiental_set.all().delete()
        prenda.transaccion_set.all().delete()
        prenda.delete()
        messages.success(request, 'Prenda eliminada correctamente.')
        return redirect('mis_prendas')
    context = {
        'usuario': usuario,
        'prenda': prenda,
    }
    return render(request, 'prendas/eliminar_prenda.html', context)

@cliente_only
def mis_prendas(request):
    """Lista todas las prendas del usuario cliente."""
    usuario = get_usuario_actual(request)
    prendas = Prenda.objects.filter(user=usuario).order_by('-fecha_publicacion')
    
    # Enriquecer cada prenda con flags de permisos
    permisos = obtener_permisos_usuario(usuario)
    prendas_enriquecidas = []
    for prenda in prendas:
        prenda_data = {
            'prenda': prenda,
            'is_owner': es_propietario_prenda(usuario, prenda),
            'can_edit': puede_editar_prenda(usuario, prenda),
            'can_delete': puede_eliminar_prenda(usuario, prenda),
        }
        prendas_enriquecidas.append(prenda_data)
    
    context = {
        'usuario': usuario,
        'prendas': prendas_enriquecidas,
        **permisos,
    }
    return render(request, 'prendas/mis_prendas.html', context)

@cliente_only
def buscar_prendas(request):
    """Búsqueda avanzada de prendas para usuarios clientes."""
    usuario = get_usuario_actual(request)
    query = request.GET.get('q', '')
    categoria = request.GET.get('categoria')
    talla = request.GET.get('talla')
    estado = request.GET.get('estado')

    prendas = Prenda.objects.filter(estado='DISPONIBLE')
    if query:
        prendas = prendas.filter(
            Q(nombre__icontains=query) |
            Q(descripcion__icontains=query)
        )
    if categoria:
        prendas = prendas.filter(categoria=categoria)
    if talla:
        prendas = prendas.filter(talla=talla)
    if estado:
        prendas = prendas.filter(estado=estado)

    context = {
        'usuario': usuario,
        'prendas': prendas.order_by('-fecha_publicacion'),
        'query': query,
        'categorias': ['Camiseta', 'Pantalón', 'Vestido', 'Chaqueta', 'Zapatos', 'Accesorios'],
        'tallas': ['XS', 'S', 'M', 'L', 'XL', 'XXL'],
        'estados': ['Nuevo', 'Excelente', 'Bueno', 'Usado'],
    }
    return render(request, 'prendas/buscar_prendas.html', context)