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

from .forms import RegistroForm, PerfilForm, PrendaForm

# Configuración de logging
logger = logging.getLogger(__name__)


# ------------------------------------------------------------------------------------------------------------------
# Impacto ambiental

@login_required_custom
def panel_impacto(request):
    """Panel de impacto ambiental de la comunidad con datos reales."""
    usuario = get_usuario_actual(request)
    
    # Obtener impacto total de la plataforma
    impacto_plataforma = obtener_impacto_total_plataforma()
    
    # Estadísticas de transacciones
    total_transacciones = Transaccion.objects.filter(estado='COMPLETADA').count()
    total_donaciones = Transaccion.objects.filter(
        tipo__nombre_tipo='Donación',
        estado='COMPLETADA'
    ).count()
    total_intercambios = Transaccion.objects.filter(
        tipo__nombre_tipo='Intercambio',
        estado='COMPLETADA'
    ).count()
    total_ventas = Transaccion.objects.filter(
        tipo__nombre_tipo='Venta',
        estado='COMPLETADA'
    ).count()

    # Top usuarios con más impacto
    from django.db.models import Sum, Count
    usuarios_activos = Usuario.objects.annotate(
        total_carbono=Sum('prenda__impactoambiental__carbono_evitar_kg'),
        num_transacciones=Count('transacciones_origen')
    ).filter(
        total_carbono__isnull=False
    ).order_by('-total_carbono')[:5]

    # Top fundaciones
    fundaciones_top = Fundacion.objects.annotate(
        num_donaciones=Count('transaccion', filter=Q(transaccion__estado='COMPLETADA'))
    ).filter(
        num_donaciones__gt=0
    ).order_by('-num_donaciones')[:5]

    context = {
        'usuario': usuario,
        'impacto_total': impacto_plataforma,
        'total_transacciones': total_transacciones,
        'total_donaciones': total_donaciones,
        'total_intercambios': total_intercambios,
        'total_ventas': total_ventas,
        'usuarios_activos': usuarios_activos,
        'fundaciones_top': fundaciones_top,
        'equivalencias': impacto_plataforma.get('equivalencias', {}),
    }
    
    return render(request, 'panel_impacto.html', context)

@login_required_custom
def mi_impacto(request):
    """Impacto ambiental personal del usuario con equivalencias."""
    usuario = get_usuario_actual(request)
    
    if not usuario:
        messages.error(request, 'Debes iniciar sesión.')
        return redirect('login')
    
    # Obtener impacto total del usuario
    impacto_usuario = obtener_impacto_total_usuario(usuario)
    
    # Mis transacciones completadas
    mis_transacciones = Transaccion.objects.filter(
        Q(user_origen=usuario) | Q(user_destino=usuario),
        estado='COMPLETADA'
    ).select_related('prenda', 'tipo', 'user_origen', 'user_destino', 'fundacion')

    # Desglose por tipo
    donaciones = mis_transacciones.filter(tipo__nombre_tipo='Donación').count()
    intercambios = mis_transacciones.filter(tipo__nombre_tipo='Intercambio').count()
    ventas = mis_transacciones.filter(tipo__nombre_tipo='Venta').count()
    
    # Ranking del usuario
    from django.db.models import Sum
    ranking = Usuario.objects.annotate(
        total_carbono=Sum('prenda__impactoambiental__carbono_evitar_kg')
    ).filter(
        total_carbono__gte=impacto_usuario['total_carbono_kg']
    ).count()

    context = {
        'usuario': usuario,
        'mi_impacto': impacto_usuario,
        'total_transacciones': mis_transacciones.count(),
        'donaciones': donaciones,
        'intercambios': intercambios,
        'ventas': ventas,
        'transacciones_recientes': mis_transacciones.order_by('-fecha_transaccion')[:10],
        'equivalencias': impacto_usuario.get('equivalencias', {}),
        'ranking': ranking,
    }
    
    return render(request, 'mi_impacto.html', context)