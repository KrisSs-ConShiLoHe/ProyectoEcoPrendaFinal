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

from .auth import get_usuario_actual

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

# Configuración de logging
logger = logging.getLogger(__name__)

def verificar_logros(usuario):
    """Chequea y asigna logros automáticamente según reglas."""
    nuevos = []

    if not usuario:
        return []
    
    for logro in Logro.objects.all():
        # Verificar si el usuario ya tiene el logro
        if UsuarioLogro.objects.filter(user=usuario, logro=logro).exists():
            continue
        
        # Logro: Donador (1 donación completada)
        if logro.codigo == 'DONADOR':
            donaciones = Transaccion.objects.filter(
                user_origen=usuario,
                tipo__nombre_tipo='Donación',
                estado='COMPLETADA'
            ).count()
            if donaciones >= 1:
                UsuarioLogro.objects.create(
                    user=usuario,
                    logro=logro,
                    fecha_desbloqueo=timezone.now()
                )
                nuevos.append(logro)
        
        # Logro: SuperUser (10 prendas publicadas)
        elif logro.codigo == 'SUPERUSER':
            prendas_count = Prenda.objects.filter(user=usuario).count()
            if prendas_count >= 10:
                UsuarioLogro.objects.create(
                    user=usuario,
                    logro=logro,
                    fecha_desbloqueo=timezone.now()
                )
                nuevos.append(logro)
        
        # Logro: Intercambiador (5 intercambios completados)
        elif logro.codigo == 'INTERCAMBIADOR':
            intercambios = Transaccion.objects.filter(
                Q(user_origen=usuario) | Q(user_destino=usuario),
                tipo__nombre_tipo='Intercambio',
                estado='COMPLETADA'
            ).count()
            if intercambios >= 5:
                UsuarioLogro.objects.create(
                    user=usuario,
                    logro=logro,
                    fecha_desbloqueo=timezone.now()
                )
                nuevos.append(logro)
        
        # Logro: Eco Guerrero (1000 kg de carbono evitado)
        elif logro.codigo == 'ECO_GUERRERO':
            impacto = ImpactoAmbiental.objects.filter(
                prenda__user=usuario
            ).aggregate(total_carbono=Sum('carbono_evitar_kg'))
            carbono_total = impacto['total_carbono'] or 0
            if carbono_total >= 1000:
                UsuarioLogro.objects.create(
                    user=usuario,
                    logro=logro,
                    fecha_desbloqueo=timezone.now()
                )
                nuevos.append(logro)
    
    return nuevos

@login_required_custom
def desbloquear_logro(request, codigo_logro):
    """Desbloqueo manual (usado para pruebas/admin)."""
    usuario = get_usuario_actual(request)
    logro = get_object_or_404(Logro, codigo=codigo_logro)
    UsuarioLogro.objects.get_or_create(user=usuario, logro=logro, defaults={'fecha_desbloqueo': timezone.now()})
    messages.success(request, f'¡Logro desbloqueado: {logro.nombre}!')
    return redirect('mis_logros')

@login_required_custom
def mis_logros(request):
    """Vista de todos los logros obtenidos por el usuario."""
    usuario = get_usuario_actual(request)
    logros = UsuarioLogro.objects.filter(user=usuario).select_related('logro')
    context = {
        'usuario': usuario,
        'logros': logros,
    }
    return render(request, 'logros/mis_logros.html', context)