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

# Configuración de logging
logger = logging.getLogger(__name__)

def configurar_cookies(request):
    """Página de configuración de cookies"""
    return render(request, 'cookies/configurar_cookies.html')

def aceptar_cookies(request):
    """Acepta todas las cookies, con preferencias personalizadas si se envían."""
    if request.method == 'POST':
        try:
            preferencias = {
                'esenciales': True,  # Siempre activadas
                'funcionalidad': request.POST.get('funcionalidad', 'true') == 'true',
                'analiticas': request.POST.get('analiticas', 'true') == 'true',
                'marketing': request.POST.get('marketing', 'true') == 'true',
                'fecha_aceptacion': timezone.now().isoformat(),
            }
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                response = JsonResponse({
                    'success': True,
                    'message': 'Preferencias de cookies guardadas',
                    'preferencias': preferencias
                })
            else:
                response = redirect('home')
            response.set_cookie(
                'cookie_consent',
                json.dumps(preferencias),
                max_age=365*24*60*60,  # 1 año
                httponly=False,  # Accesible desde JS
                samesite='Lax'
            )
            return response
        except Exception as e:
            logger.error(f"Error aceptando cookies: {e}")
            return JsonResponse({'error': 'Error interno'}, status=500)
    return redirect('configurar_cookies')

def rechazar_cookies(request):
    """Rechaza cookies no esenciales y guarda la preferencia mínima."""
    if request.method == 'POST':
        try:
            preferencias = {
                'esenciales': True,
                'funcionalidad': False,
                'analiticas': False,
                'marketing': False,
                'fecha_rechazo': timezone.now().isoformat(),
            }
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                response = JsonResponse({
                    'success': True,
                    'message': 'Solo se usarán cookies esenciales',
                    'preferencias': preferencias
                })
            else:
                response = redirect('home')
            response.set_cookie(
                'cookie_consent',
                json.dumps(preferencias),
                max_age=365*24*60*60,
                httponly=False,
                samesite='Lax'
            )
            return response
        except Exception as e:
            logger.error(f"Error rechazando cookies: {e}")
            return JsonResponse({'error': 'Error interno'}, status=500)
    return redirect('configurar_cookies')

def obtener_preferencias_cookies(request):
    """Devuelve las preferencias de cookies actuales (API)"""
    cookie_consent = request.COOKIES.get('cookie_consent')
    if cookie_consent:
        try:
            preferencias = json.loads(cookie_consent)
            return JsonResponse({
                'configurado': True,
                'preferencias': preferencias
            })
        except json.JSONDecodeError:
            logger.warning(f"Error decodificando cookie_consent: {cookie_consent}")
    return JsonResponse({
        'configurado': False,
        'preferencias': None
    })

def eliminar_cookies(request):
    """Elimina cookies no esenciales y restablece preferencias."""
    if request.method == 'POST':
        try:
            response = JsonResponse({
                'success': True,
                'message': 'Cookies eliminadas. Por favor configura tus preferencias nuevamente.'
            })
            response.delete_cookie('cookie_consent')
            # Eliminar todas menos las esenciales (puedes adaptar la lista de esenciales a tu configuración)
            for cookie_name in list(request.COOKIES.keys()):
                if cookie_name not in ['csrftoken', 'sessionid', 'ecoprendas_sessionid']:
                    response.delete_cookie(cookie_name)
            return response
        except Exception as e:
            logger.error(f"Error eliminando cookies: {e}")
            return JsonResponse({'error': 'Error interno'}, status=500)
    return JsonResponse({'error': 'Método no permitido'}, status=405)