"""
Vistas faltantes para EcoPrenda:
- galeria_imagenes: Galería de imágenes con Cloudinary
- informe_impacto: Informe de impacto ambiental
- comparador_impacto: Comparador de impacto entre usuarios
- api_calcular_impacto: API para calcular impacto
- api_sugerir_categoria: API para sugerir categoría con Clarifai
"""
# views que se me olvidaron agregar antes XD

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Sum, Count, Avg
from django.utils import timezone
import json
import logging

from .models import (
    Usuario, Prenda, Transaccion, TipoTransaccion,
    Fundacion, Mensaje, ImpactoAmbiental,
    Logro, UsuarioLogro, CampanaFundacion
)
from .decorators import (
    login_required_custom,
    ajax_login_required,
)
from ..cloudinary_utils import subir_imagen_prenda
from ..clarifai_utils import sugerir_categoria_automatica
from .carbon_utils import (
    calcular_impacto_prenda,
    calcular_impacto_transaccion,
    obtener_impacto_total_usuario,
    obtener_impacto_total_plataforma,
    generar_informe_impacto,
    formatear_equivalencia
)
from .forms import PrendaForm
from django.conf import settings

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------------------------------------------------------
# GALERÍA DE IMÁGENES - Integración con Cloudinary y Clarifai
# ------------------------------------------------------------------------------------------------------------------

@login_required_custom
def galeria_imagenes(request):
    """
    Vista de galería de imágenes con Cloudinary
    Muestra todas las imágenes subidas por el usuario
    """
    try:
        usuario = Usuario.objects.get(usuario=request.session.get('usuario'))
    except Usuario.DoesNotExist:
        return redirect('login')

    # Obtener todas las prendas del usuario para la galería
    prendas = Prenda.objects.filter(propietario=usuario).select_related('propietario')

    # Agrupar por imagen para galería
    imagenes = []
    for prenda in prendas:
        if prenda.imagen:
            imagenes.append({
                'url': prenda.imagen,
                'prenda_id': prenda.id_prenda,
                'nombre': prenda.nombre,
                'categoria': prenda.categoria,
                'fecha': prenda.fecha_publicacion
            })

    context = {
        'usuario': usuario,
        'imagenes': imagenes,
        'total_imagenes': len(imagenes),
        'cloudinary_cloud_name': settings.CLOUDINARY_CLOUD_NAME,
    }

    logger.info(f"✅ Galería de imágenes visualizada por {usuario.usuario} - {len(imagenes)} imágenes")
    return render(request, 'prendas/galeria_imagenes.html', context)


# ------------------------------------------------------------------------------------------------------------------
# INFORME DE IMPACTO AMBIENTAL
# ------------------------------------------------------------------------------------------------------------------

@login_required_custom
def informe_impacto(request):
    """
    Vista que muestra un informe detallado del impacto ambiental del usuario
    Incluye:
    - Emisiones de CO2 evitadas
    - Agua ahorrada
    - Residuos evitados
    - Gráficos de tendencia
    """
    try:
        usuario = Usuario.objects.get(usuario=request.session.get('usuario'))
    except Usuario.DoesNotExist:
        return redirect('login')

    # Calcular impacto total del usuario
    impacto_total = obtener_impacto_total_usuario(usuario)

    # Obtener todas las transacciones del usuario
    transacciones = Transaccion.objects.filter(
        Q(comprador=usuario) | Q(vendedor=usuario)
    ).select_related('prenda', 'tipo_transaccion')

    # Generar informe
    informe = generar_informe_impacto(usuario)

    # Estadísticas por mes
    impactos_por_mes = ImpactoAmbiental.objects.filter(
        usuario=usuario
    ).values('fecha_registro__month').annotate(
        total_co2=Sum('emisiones_co2_evitadas'),
        total_agua=Sum('agua_ahorrada'),
        total_residuos=Sum('residuos_evitados')
    ).order_by('fecha_registro__month')

    context = {
        'usuario': usuario,
        'impacto_total': impacto_total,
        'transacciones': transacciones,
        'informe': informe,
        'impactos_por_mes': impactos_por_mes,
        'equivalencias': {
            'arboles': impacto_total.get('arboles_plantados', 0),
            'viajes_auto': impacto_total.get('viajes_auto_evitados', 0),
            'duchas': impacto_total.get('duchas_ahorradas', 0),
        }
    }

    logger.info(f"📊 Informe de impacto generado para {usuario.usuario}")
    return render(request, 'impacto ambiental/informe_impacto.html', context)


# ------------------------------------------------------------------------------------------------------------------
# COMPARADOR DE IMPACTO AMBIENTAL
# ------------------------------------------------------------------------------------------------------------------

@login_required_custom
def comparador_impacto(request):
    """
    Vista que compara el impacto ambiental del usuario con otros usuarios
    y con el promedio de la plataforma
    """
    try:
        usuario = Usuario.objects.get(usuario=request.session.get('usuario'))
    except Usuario.DoesNotExist:
        return redirect('login')

    # Impacto del usuario actual
    impacto_usuario = obtener_impacto_total_usuario(usuario)

    # Impacto total de la plataforma
    impacto_plataforma = obtener_impacto_total_plataforma()

    # Top 5 usuarios por impacto
    usuarios_top = Usuario.objects.annotate(
        total_co2=Sum('impactoambiental__emisiones_co2_evitadas')
    ).filter(
        total_co2__isnull=False
    ).order_by('-total_co2')[:5]

    # Datos para gráficos
    comparacion = {
        'usuario': impacto_usuario,
        'plataforma': impacto_plataforma,
        'posicion': usuarios_top.filter(id_usuario=usuario.id_usuario).first(),
        'top_5': usuarios_top,
    }

    context = {
        'usuario': usuario,
        'comparacion': comparacion,
        'usuarios_top': usuarios_top,
    }

    logger.info(f"📈 Comparador de impacto visualizado por {usuario.usuario}")
    return render(request, 'impacto ambiental/comparador_impacto.html', context)


# ------------------------------------------------------------------------------------------------------------------
# API: CALCULAR IMPACTO AMBIENTAL
# ------------------------------------------------------------------------------------------------------------------

@ajax_login_required
def api_calcular_impacto(request):
    """
    API para calcular impacto ambiental de una prenda
    Recibe: prenda_id
    Retorna: JSON con cálculos de CO2, agua, residuos
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            prenda_id = data.get('prenda_id')

            prenda = get_object_or_404(Prenda, id_prenda=prenda_id)

            # Calcular impacto
            impacto = calcular_impacto_prenda(prenda)

            logger.info(f"✅ Impacto calculado para prenda {prenda_id}")

            return JsonResponse({
                'success': True,
                'impacto': {
                    'co2': impacto.get('emisiones_co2_evitadas', 0),
                    'agua': impacto.get('agua_ahorrada', 0),
                    'residuos': impacto.get('residuos_evitados', 0),
                    'equivalencias': {
                        'arboles': formatear_equivalencia('arboles', impacto.get('emisiones_co2_evitadas', 0)),
                        'viajes': formatear_equivalencia('viajes_auto', impacto.get('emisiones_co2_evitadas', 0)),
                        'duchas': formatear_equivalencia('duchas', impacto.get('agua_ahorrada', 0)),
                    }
                }
            })
        except Exception as e:
            logger.error(f"❌ Error al calcular impacto: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)

    return JsonResponse({'error': 'Método no permitido'}, status=405)


# ------------------------------------------------------------------------------------------------------------------
# API: SUGERIR CATEGORÍA CON CLARIFAI
# ------------------------------------------------------------------------------------------------------------------

@ajax_login_required
def api_sugerir_categoria(request):
    """
    API para sugerir categoría de prenda usando Clarifai
    Recibe: imagen (URL o base64)
    Retorna: JSON con sugerencia de categoría y confianza
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            imagen_url = data.get('imagen_url')
            imagen_bytes = data.get('imagen_bytes')  # Si se envía en base64

            if not imagen_url and not imagen_bytes:
                return JsonResponse({
                    'success': False,
                    'error': 'Se requiere imagen_url o imagen_bytes'
                }, status=400)

            # Usar Clarifai para sugerir categoría
            categoria_sugerida = sugerir_categoria_automatica(
                imagen_url=imagen_url,
                imagen_bytes=imagen_bytes
            )

            logger.info(f"✅ Categoría sugerida por Clarifai: {categoria_sugerida}")

            return JsonResponse({
                'success': True,
                'categoria': categoria_sugerida['categoria'],
                'confianza': categoria_sugerida['confianza'],
                'detalles': categoria_sugerida
            })

        except Exception as e:
            logger.error(f"❌ Error al sugerir categoría con Clarifai: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': f"Error en Clarifai: {str(e)}"
            }, status=400)

    return JsonResponse({'error': 'Método no permitido'}, status=405)
