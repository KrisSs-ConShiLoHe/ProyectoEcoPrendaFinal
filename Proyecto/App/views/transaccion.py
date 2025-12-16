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
    extraer_public_id_de_url
)

from ..carbon_utils import (
    calcular_impacto_prenda,
    calcular_impacto_transaccion,
    obtener_impacto_total_usuario,
    obtener_impacto_total_plataforma,
    generar_informe_impacto,
    formatear_equivalencia
)

from ..forms import RegistroForm, PerfilForm, PrendaForm
from .auth import get_usuario_actual, puede_actualizar_transaccion
from .logro import verificar_logros

# Configuración de logging
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------------------------------------------
# Transacciones

@login_required_custom
def proponer_intercambio(request, id_prenda):
    """Permite a un usuario proponer un intercambio por otra prenda."""
    usuario = get_usuario_actual(request)
    prenda_destino = get_object_or_404(Prenda.objects.select_related('user'), id_prenda=id_prenda)  # Cambiado: 'pk=id_prenda', agregado select_related

    if prenda_destino.user.id == usuario.id_usuario:  # Cambiado: 'prenda_destino.user.id == usuario.id'
        messages.error(request, 'No puedes intercambiar con tu propia prenda.')
        return redirect('detalle_prenda', id_prenda=id_prenda)
    if prenda_destino.estado != 'DISPONIBLE':  # Cambiado: check directo en 'estado'
        messages.error(request, f'Esta prenda ya no está disponible para intercambio ({prenda_destino.get_estado_display()}).')
        return redirect('detalle_prenda', id_prenda=id_prenda)

    if request.method == 'POST':
        prenda_origen_id = request.POST.get('prenda_origen')
        prenda_origen = get_object_or_404(Prenda, pk=prenda_origen_id, user=usuario)  # Cambiado: 'pk=prenda_origen_id', 'user=usuario'
        if prenda_origen.estado != 'DISPONIBLE':  # Cambiado: check directo
            messages.error(request, 'La prenda ofrecida ya no está disponible.')
            return redirect('detalle_prenda', id_prenda=id_prenda)
        tipo_intercambio, _ = TipoTransaccion.objects.get_or_create(nombre_tipo='Intercambio', defaults={
            'descripcion': 'Intercambio de prendas entre usuarios'
        })
        try:
            transaccion = Transaccion.objects.create(
                prenda=prenda_destino,  # Cambiado: 'prenda=prenda_destino'
                tipo=tipo_intercambio,  # Cambiado: 'tipo=tipo_intercambio'
                user_origen=usuario,  # Cambiado: 'user_origen=usuario'
                user_destino=prenda_destino.user,  # Cambiado: 'user_destino=prenda_destino.user'
                fecha_transaccion=timezone.now(),
                estado='PENDIENTE'
            )
            messages.success(request, f'¡Intercambio propuesto! Código de seguimiento: {transaccion.id}. Ahora puedes negociar con el otro usuario.')  # Cambiado: 'transaccion.id'
            return redirect('conversacion', id_usuario=prenda_destino.user.id)  # Cambiado: 'prenda_destino.user.id'
        except Exception as e:
            logger.error(f"Error creando intercambio para usuario {usuario.id_usuario}: {e}")
            messages.error(request, 'Error interno. Intenta nuevamente.')

    mis_prendas_usuario = Prenda.objects.filter(user=usuario, estado='DISPONIBLE')  # Cambiado: 'user=usuario', 'estado'
    context = {
        'usuario': usuario,
        'prenda_destino': prenda_destino,
        'mis_prendas': mis_prendas_usuario,
    }
    return render(request, 'transacciones/proponer_intercambio.html', context)

@login_required_custom
def marcar_intercambio_entregado(request, id_transaccion):
    usuario = get_usuario_actual(request)
    transaccion = get_object_or_404(Transaccion.objects.select_related('prenda', 'user_origen'), id=id_transaccion)  # Cambiado: agregado select_related
    
    permitido, error = puede_actualizar_transaccion(usuario, transaccion, 'origen')
    if not permitido:
        return JsonResponse({'error': error}, status=403)
    if transaccion.estado != 'RESERVADA':
        return JsonResponse({'error': 'La transacción no está en estado reservado.'}, status=400)
    
    try:
        transaccion.marcar_en_proceso()
        messages.success(request, 'Has marcado la prenda como entregada.')
        return redirect('mis_transacciones')
    except Exception as e:
        logger.error(f"Error marcando intercambio entregado {transaccion.id}: {e}")
        return JsonResponse({'error': 'Error interno'}, status=500)

@login_required_custom
def confirmar_recepcion_intercambio(request, id_transaccion):
    usuario = get_usuario_actual(request)
    transaccion = get_object_or_404(Transaccion.objects.select_related('prenda', 'user_destino'), id=id_transaccion)  # Cambiado: agregado select_related
    
    permitido, error = puede_actualizar_transaccion(usuario, transaccion, 'destino')
    if not permitido:
        return JsonResponse({'error': error}, status=403)
    if transaccion.estado != 'EN_PROCESO':
        return JsonResponse({'error': 'Debes esperar a que el propietario marque como entregada.'}, status=400)
    
    try:
        transaccion.marcar_como_completada()
        messages.success(request, '¡Intercambio completado con éxito!')
        return redirect('mis_transacciones')
    except Exception as e:
        logger.error(f"Error confirmando recepción intercambio {transaccion.id}: {e}")
        return JsonResponse({'error': 'Error interno'}, status=500)

@login_required_custom
def cancelar_intercambio(request, id_transaccion):
    usuario = get_usuario_actual(request)
    transaccion = get_object_or_404(Transaccion.objects.select_related('prenda'), id=id_transaccion)  # Cambiado: agregado select_related
    
    permitido, error = puede_actualizar_transaccion(usuario, transaccion, 'origen')
    if not permitido:
        return JsonResponse({'error': error}, status=403)
    if transaccion.estado not in ['PENDIENTE', 'RESERVADA', 'EN_PROCESO']:
        return JsonResponse({'error': 'No puedes cancelar una transacción finalizada.'}, status=400)
    
    try:
        transaccion.cancelar()
        messages.success(request, 'Intercambio cancelado y prenda devuelta a disponible.')
        return redirect('mis_transacciones')
    except Exception as e:
        logger.error(f"Error cancelando intercambio {transaccion.id}: {e}")
        return JsonResponse({'error': 'Error interno'}, status=500)

@login_required_custom
def comprar_prenda(request, id_prenda):
    """Proponer compra de una prenda."""
    usuario = get_usuario_actual(request)
    prenda = get_object_or_404(Prenda.objects.select_related('user'), id_prenda=id_prenda)  # Cambiado: agregado select_related
    
    if prenda.user.id == usuario.id_usuario:  # Cambiado: 'prenda.user.id == usuario.id'
        messages.error(request, "No puedes comprar tu propia prenda.")
        return redirect('detalle_prenda', id_prenda=id_prenda)
    if prenda.estado != 'DISPONIBLE':  # Cambiado: check directo
        messages.error(request, "Esta prenda ya no está disponible.")
        return redirect('detalle_prenda', id_prenda=id_prenda)

    if request.method == 'POST':
        tipo_venta, _ = TipoTransaccion.objects.get_or_create(
            nombre_tipo='Venta', defaults={'descripcion': 'Venta de prenda entre usuarios'}
        )
        try:
            transaccion = Transaccion.objects.create(
                prenda=prenda,  # Cambiado: 'prenda=prenda'
                tipo=tipo_venta,  # Cambiado: 'tipo=tipo_venta'
                user_origen=prenda.user,  # Cambiado: 'user_origen=prenda.user'
                user_destino=usuario,  # Cambiado: 'user_destino=usuario'
                fecha_transaccion=timezone.now(),
                estado='PENDIENTE'
            )
            messages.success(request, f'Solicitud de compra enviada. Código: {transaccion.id}. Ahora puedes negociar con el vendedor.')  # Cambiado: 'transaccion.id'
            return redirect('conversacion', id_usuario=prenda.user.id)  # Cambiado: 'prenda.user.id'
        except Exception as e:
            logger.error(f"Error creando compra para usuario {usuario.id_usuario}: {e}")
            messages.error(request, 'Error interno. Intenta nuevamente.')
    
    context = {"usuario": usuario, "prenda": prenda}
    return render(request, 'transacciones/comprar_prenda.html', context)

@login_required_custom
def marcar_compra_entregado(request, id_transaccion):
    usuario = get_usuario_actual(request)
    transaccion = get_object_or_404(Transaccion.objects.select_related('prenda', 'user_origen'), id=id_transaccion)  # Cambiado: agregado select_related
    
    permitido, error = puede_actualizar_transaccion(usuario, transaccion, 'origen')
    if not permitido:
        return JsonResponse({'error': error}, status=403)
    if transaccion.estado != 'RESERVADA':
        return JsonResponse({'error': 'La transacción no está en estado reservado.'}, status=400)
    
    try:
        transaccion.marcar_en_proceso()
        messages.success(request, 'Has marcado la prenda como entregada.')
        return redirect('mis_transacciones')
    except Exception as e:
        logger.error(f"Error marcando compra entregada {transaccion.id}: {e}")
        return JsonResponse({'error': 'Error interno'}, status=500)

@login_required_custom
def marcar_donacion_enviada(request, id_transaccion):
    """Permite al donante marcar su donación como enviada."""
    usuario = get_usuario_actual(request)
    transaccion = get_object_or_404(Transaccion.objects.select_related('prenda', 'user_origen'), id=id_transaccion)  # Cambiado: agregado select_related

    permitido, error = puede_actualizar_transaccion(usuario, transaccion, 'origen')
    if not permitido:
        return JsonResponse({'error': error}, status=403)
    if not transaccion.es_donacion():
        return JsonResponse({'error': 'Esta acción solo aplica a donaciones.'}, status=400)
    if transaccion.estado not in ['PENDIENTE', 'RESERVADA']:
        return JsonResponse({'error': 'La transacción no está en un estado válido para marcar como enviada.'}, status=400)

    try:
        transaccion.marcar_en_proceso()
        messages.success(request, 'Has marcado la donación como enviada. La fundación confirmará la recepción.')
        return redirect('mis_transacciones')
    except Exception as e:
        logger.error(f"Error marcando donación enviada {transaccion.id}: {e}")
        return JsonResponse({'error': 'Error interno'}, status=500)

@login_required_custom
def confirmar_recepcion_compra(request, id_transaccion):
    usuario = get_usuario_actual(request)
    transaccion = get_object_or_404(Transaccion.objects.select_related('prenda', 'user_destino'), id=id_transaccion)  # Cambiado: agregado select_related
    
    permitido, error = puede_actualizar_transaccion(usuario, transaccion, 'destino')
    if not permitido:
        return JsonResponse({'error': error}, status=403)
    if transaccion.estado != 'EN_PROCESO':
        return JsonResponse({'error': 'Solo puedes confirmar si ya fue marcada como entregada.'}, status=400)
    
    try:
        transaccion.marcar_como_completada()
        messages.success(request, '¡Transacción completada con éxito!')
        return redirect('mis_transacciones')
    except Exception as e:
        logger.error(f"Error confirmando recepción compra {transaccion.id}: {e}")
        return JsonResponse({'error': 'Error interno'}, status=500)

@login_required_custom
def cancelar_compra(request, id_transaccion):
    usuario = get_usuario_actual(request)
    transaccion = get_object_or_404(Transaccion.objects.select_related('prenda'), id=id_transaccion)  # Cambiado: agregado select_related
    
    permitido, error = puede_actualizar_transaccion(usuario, transaccion, 'origen')
    if not permitido:
        return JsonResponse({'error': error}, status=403)
    if transaccion.estado not in ['PENDIENTE', 'RESERVADA', 'EN_PROCESO']:
        return JsonResponse({'error': 'No puedes cancelar una transacción finalizada.'}, status=400)
    
    try:
        transaccion.cancelar()
        messages.success(request, 'Transacción cancelada y prenda devuelta a disponible.')
        return redirect('mis_transacciones')
    except Exception as e:
        logger.error(f"Error cancelando compra {transaccion.id}: {e}")
        return JsonResponse({'error': 'Error interno'}, status=500)

@login_required_custom
def donar_prenda(request, id_prenda):
    """Permite a un usuario donar una prenda propia a una fundación activa."""
    usuario = get_usuario_actual(request)
    prenda = get_object_or_404(Prenda.objects.select_related('user'), pk=id_prenda)  # Cambiado: agregado select_related
    if prenda.user.id != usuario.id_usuario:  # Cambiado: 'prenda.user.id != usuario.id'
        messages.error(request, 'Solo puedes donar tus propias prendas.')
        return redirect('detalle_prenda', id_prenda=id_prenda)
    if prenda.estado != 'DISPONIBLE':  # Cambiado: check directo
        messages.error(request, 'Esta prenda ya no está disponible.')
        return redirect('detalle_prenda', id_prenda=id_prenda)
    if request.method == 'POST':
        fundacion_id = request.POST.get('fundacion')
        if not fundacion_id:
            messages.error(request, 'Debes seleccionar una fundación válida.')
            return redirect('donar_prenda', id_prenda=id_prenda)
        fundacion = get_object_or_404(Fundacion.objects.select_related('representante'), pk=fundacion_id, activa=True)  # Cambiado: agregado select_related
        tipo_donacion, _ = TipoTransaccion.objects.get_or_create(nombre_tipo='Donación', defaults={
            'descripcion': 'Donación de prenda a fundación'
        })
        try:
            transaccion = Transaccion.objects.create(
                prenda=prenda,  # Cambiado: 'prenda=prenda'
                tipo=tipo_donacion,  # Cambiado: 'tipo=tipo_donacion'
                user_origen=usuario,  # Cambiado: 'user_origen=usuario'
                fundacion=fundacion,  # Cambiado: 'fundacion=fundacion'
                fecha_transaccion=timezone.now(),
                estado='PENDIENTE'
            )
            prenda.marcar_como_reservada()
            # Verificar logros
            nuevos_logros = verificar_logros(usuario)  # Asumiendo que existe
            if nuevos_logros:
                for logro in nuevos_logros:
                    messages.success(request, f'🏆 ¡Nuevo logro desbloqueado: {logro.nombre}!')
            messages.success(request, f'¡Prenda donada exitosamente a {fundacion.nombre}! Código de seguimiento: {transaccion.id}')  # Cambiado: 'transaccion.id'
            return redirect('mis_transacciones')
        except Exception as e:
            logger.error(f"Error donando prenda {prenda.pk} por usuario {usuario.id_usuario}: {e}")
            messages.error(request, 'Error interno. Intenta nuevamente.')
    fundaciones = Fundacion.objects.filter(activa=True)
    context = {
        'usuario': usuario,
        'prenda': prenda,
        'fundaciones': fundaciones,
    }
    return render(request, 'transacciones/donar_prenda.html', context)

@login_required_custom
def mis_transacciones(request):
    usuario = get_usuario_actual(request)

    if usuario.es_representante_fundacion():
        messages.error(request, 'Como representante de fundación, no puedes acceder a tus transacciones personales.')
        return redirect('home')

    transacciones_enviadas = Transaccion.objects.filter(
        user_origen=usuario  # Cambiado: 'user_origen=usuario'
    ).select_related('prenda', 'tipo', 'user_destino', 'fundacion')  # Agregado select_related
    
    transacciones_recibidas = Transaccion.objects.filter(
        user_destino=usuario  # Cambiado: 'user_destino=usuario'
    ).exclude(
        fundacion__isnull=False  # Cambiado: 'fundacion__isnull=False'
    ).select_related('prenda', 'tipo', 'user_origen')  # Agregado select_related
    
    context = {
        "usuario": usuario,
        "transacciones_enviadas": transacciones_enviadas,
        "transacciones_recibidas": transacciones_recibidas,
    }
    return render(request, 'transacciones/mis_transacciones.html', context)

@login_required_custom
def actualizar_estado_transaccion(request, id_transaccion):
    """Permite actualizar el estado de una transacción."""
    usuario = get_usuario_actual(request)
    transaccion = get_object_or_404(Transaccion.objects.select_related('prenda', 'user_destino', 'user_origen'), id=id_transaccion)  # Cambiado: agregado select_related
    if transaccion.user_destino and transaccion.user_destino.id != usuario.id_usuario:  # Cambiado: 'user_destino'
        if transaccion.user_origen.id != usuario.id_usuario:  # Cambiado: 'user_origen'
            return JsonResponse({'error': 'No autorizado'}, status=403)
    
    if request.method == 'POST':
        nuevo_estado = request.POST.get('estado')
        if not nuevo_estado or nuevo_estado not in dict(Transaccion.ESTADO_CHOICES):
            return JsonResponse({'error': 'Estado inválido'}, status=400)
        
        if transaccion.estado == 'PENDIENTE':
            if nuevo_estado == 'ACEPTADA':
                try:
                    transaccion.prenda.marcar_como_reservada()  # Cambiado: 'prenda'
                    transaccion.estado = nuevo_estado
                    transaccion.save()
                    messages.success(request, 'Has aceptado la propuesta. La prenda ahora está reservada.')
                except Exception as e:
                    logger.error(f"Error aceptando transacción {transaccion.id}: {e}")
                    return JsonResponse({'error': 'Error interno'}, status=500)
            elif nuevo_estado == 'RECHAZADA':
                try:
                    transaccion.estado = nuevo_estado
                    transaccion.save()
                    messages.success(request, 'Has rechazado la propuesta. La prenda sigue disponible.')
                except Exception as e:
                    logger.error(f"Error rechazando transacción {transaccion.id}: {e}")
                    return JsonResponse({'error': 'Error interno'}, status=500)
            else:
                return JsonResponse({'error': 'Desde PENDIENTE solo puedes aceptar (ACEPTADA) o rechazar (RECHAZADA).'}, status=400)
        else:
            try:
                transaccion.estado = nuevo_estado
                transaccion.save()
                messages.success(request, f'Estado de la transacción actualizado a: {transaccion.get_estado_display()}')
            except Exception as e:
                logger.error(f"Error actualizando estado transacción {transaccion.id}: {e}")
                return JsonResponse({'error': 'Error interno'}, status=500)
        
        return redirect('mis_transacciones')
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@login_required_custom
def reportar_disputa(request, id_transaccion):
    """Permite al comprador/receptor reportar un problema con la prenda."""
    usuario = get_usuario_actual(request)
    transaccion = get_object_or_404(Transaccion.objects.select_related('prenda', 'user_destino'), id=id_transaccion)  # Cambiado: agregado select_related
    
    if not transaccion.user_destino or transaccion.user_destino.id != usuario.id_usuario:  # Cambiado: 'user_destino'
        messages.error(request, 'Solo el receptor puede reportar problemas.')
        return redirect('mis_transacciones')
    
    if transaccion.estado != 'EN_PROCESO':
        messages.error(request, 'Solo puedes reportar problemas cuando la prenda está en proceso de entrega.')
        return redirect('mis_transacciones')
    
    if request.method == 'POST':
        razon = request.POST.get('razon_disputa')
        if not razon or len(razon.strip()) < 10:
            messages.error(request, 'Debes proporcionar una descripción detallada del problema (mínimo 10 caracteres).')
            return redirect('mis_transacciones')
        
        try:
            transaccion.estado = 'EN_DISPUTA'
            transaccion.en_disputa = True
            transaccion.razon_disputa = razon.strip()
            transaccion.reportado_por = usuario
            transaccion.fecha_disputa = timezone.now()
            transaccion.save()
            messages.success(request, 'Tu reporte ha sido registrado. El equipo de administración revisará la disputa.')
            return redirect('mis_transacciones')
        except Exception as e:
            logger.error(f"Error reportando disputa en transacción {transaccion.id}: {e}")
            messages.error(request, 'Error interno. Intenta nuevamente.')
    
    context = {
        'usuario': usuario,
        'transaccion': transaccion,
    }
    return render(request, 'reportes/reportar_disputa.html', context)

@admin_required
def resolver_disputa(request, id_transaccion):
    """Solo administrador: Resuelve una disputa."""
    transaccion = get_object_or_404(Transaccion.objects.select_related('prenda', 'user_origen', 'user_destino', 'reportado_por'), pk=id_transaccion)  # Cambiado: agregado select_related
    
    if transaccion.estado != 'EN_DISPUTA':
        messages.error(request, 'Esta transacción no está en disputa.')
        return redirect('admin:index')
    
    if request.method == 'POST':
        resolucion = request.POST.get('resolucion')
        notas_admin = request.POST.get('notas_admin')
        
        if resolucion not in ['COMPLETADA', 'CANCELADA']:
            return JsonResponse({'error': 'Resolución inválida'}, status=400)
        
        try:
            transaccion.estado = resolucion
            transaccion.save()
            messages.success(request, f'Disputa resuelta como {transaccion.get_estado_display()}')
            return redirect('admin:index')
        except Exception as e:
            logger.error(f"Error resolviendo disputa en transacción {transaccion.id}: {e}")
            return JsonResponse({'error': 'Error interno'}, status=500)
    
    # Obtener mensajes entre los usuarios
    mensajes = Mensaje.objects.filter(
        Q(emisor=transaccion.user_origen, receptor=transaccion.user_destino) |  # Cambiado: 'emisor', 'receptor'
        Q(emisor=transaccion.user_destino, receptor=transaccion.user_origen)
    ).order_by('fecha_envio')
    
    context = {
        'transaccion': transaccion,
        'mensajes': mensajes,
    }
    return render(request, 'reportes/admin_resolver_disputa.html', context)