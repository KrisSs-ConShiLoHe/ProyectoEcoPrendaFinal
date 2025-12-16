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

# ------------------------------------------------------------------------------------------------------------------
# Campañas solidarias

@representante_fundacion_required
def crear_campana(request):
    """Permite a la fundación/representante crear una nueva campaña."""
    usuario = get_usuario_actual(request)
    fundacion = usuario.fundacion_asignada
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')
        fecha_inicio = request.POST.get('fecha_inicio')
        fecha_fin = request.POST.get('fecha_fin')
        objetivo_prendas = int(request.POST.get('objetivo_prendas', 0))
        if not all([nombre, fecha_inicio, fecha_fin, objetivo_prendas > 0]):
            messages.error(request, 'Completa los campos obligatorios y un objetivo mayor a 0.')
        else:
            CampanaFundacion.objects.create(
                fundacion=fundacion,
                nombre=nombre,
                descripcion=descripcion,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                objetivo_prendas=objetivo_prendas,
                activa=True
            )
            messages.success(request, '¡Campaña creada exitosamente!')
            return redirect('panel_fundacion')
    context = {'usuario': usuario, 'fundacion': fundacion}
    return render(request, 'campañas/crear_campana.html', context)

@login_required_custom
def campanas_solidarias(request):
    """Muestra todas las campañas solidarias activas de fundaciones."""
    usuario = get_usuario_actual(request)
    campanas = CampanaFundacion.objects.filter(activa=True).select_related('fundacion').order_by('fecha_inicio')
    context = {
        'usuario': usuario,
        'campanas': campanas,
    }
    return render(request, 'campañas/campanas_solidarias.html', context)

@login_required_custom
def detalle_campana(request, id):
    """Detalle de una campaña solidaria de una fundación."""
    usuario = get_usuario_actual(request)
    campana = get_object_or_404(CampanaFundacion, pk=id)
    donaciones = Transaccion.objects.filter(campana=campana, tipo__nombre_tipo='Donación', estado='COMPLETADA')
    prendas_donadas = [don.prenda for don in donaciones if don.prenda]
    avance = len(prendas_donadas)
    porcentaje_avance = int(100 * avance / campana.objetivo_prendas) if campana.objetivo_prendas and campana.objetivo_prendas > 0 else 0
    context = {
        'usuario': usuario,
        'campana': campana,
        'donaciones': donaciones,
        'avance': avance,
        'porcentaje_avance': porcentaje_avance,
    }
    return render(request, 'campañas/detalle_campana.html', context)

@login_required_custom
def donar_a_campana(request, id):
    """Permite donar una prenda a una campaña solidaria."""
    usuario = get_usuario_actual(request)
    campana = get_object_or_404(CampanaFundacion, pk=id, activa=True)
    if request.method == 'POST':
        prenda_id = request.POST.get('prenda_id')
        prenda = get_object_or_404(Prenda, pk=prenda_id, user=usuario, estado='DISPONIBLE')
        if not prenda.esta_disponible():
            messages.error(request, 'La prenda ya no está disponible.')
            return redirect('donar_a_campana', id=id)
        tipo_donacion, _ = TipoTransaccion.objects.get_or_create(nombre_tipo='Donación')
        Transaccion.objects.create(
            prenda=prenda,
            tipo=tipo_donacion,
            user_origen=usuario,
            fundacion=campana.fundacion,
            campana=campana,
            fecha_transaccion=timezone.now(),
            estado='PENDIENTE'
        )
        prenda.estado = 'RESERVADA'
        prenda.save()
        messages.success(request, f'¡Donación asociada a la campaña "{campana.nombre}"!')
        return redirect('mis_prendas')
    prendas_usuario = Prenda.objects.filter(user=usuario, estado='DISPONIBLE')
    context = {
        'usuario': usuario,
        'campana': campana,
        'prendas': prendas_usuario,
    }
    return render(request, 'campañas/donar_a_campana.html', context)

@representante_fundacion_required
def mis_campanas(request):
    """Lista de campañas gestionadas por la fundación del usuario."""
    usuario = get_usuario_actual(request)
    fundacion = usuario.fundacion_asignada
    campanas = CampanaFundacion.objects.filter(fundacion=fundacion)
    context = {
        'usuario': usuario,
        'fundacion': fundacion,
        'campanas': campanas,
    }
    return render(request, 'campañas/mis_campanas.html', context)

@representante_fundacion_required
def editar_campana(request, id):
    """Permite editar una campaña existente."""
    usuario = get_usuario_actual(request)
    campana = get_object_or_404(CampanaFundacion, pk=id, fundacion=usuario.fundacion_asignada)

    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')
        fecha_inicio = request.POST.get('fecha_inicio')
        fecha_fin = request.POST.get('fecha_fin')
        objetivo_prendas = int(request.POST.get('objetivo_prendas', 0))
        categorias_solicitadas = request.POST.get('categorias_solicitadas', '')

        if not all([nombre, fecha_inicio, fecha_fin, objetivo_prendas > 0]):
            messages.error(request, 'Completa los campos obligatorios y un objetivo mayor a 0.')
        else:
            campana.nombre = nombre
            campana.descripcion = descripcion
            campana.fecha_inicio = fecha_inicio
            campana.fecha_fin = fecha_fin
            campana.objetivo_prendas = objetivo_prendas
            campana.categorias_solicitadas = categorias_solicitadas
            campana.save()
            messages.success(request, '¡Campaña actualizada exitosamente!')
            return redirect('mis_campanas')

    context = {
        'usuario': usuario,
        'campana': campana,
        'fundacion': usuario.fundacion_asignada
    }
    return render(request, 'campañas/editar_campana.html', context)

@representante_fundacion_required
def eliminar_campana(request, id):
    """Permite eliminar una campaña."""
    usuario = get_usuario_actual(request)
    campana = get_object_or_404(CampanaFundacion, pk=id, fundacion=usuario.fundacion_asignada)

    if request.method == 'POST':
        campana.delete()
        messages.success(request, 'Campaña eliminada exitosamente.')
        return redirect('mis_campanas')

    context = {
        'usuario': usuario,
        'campana': campana,
        'fundacion': usuario.fundacion_asignada
    }
    return render(request, 'campañas/eliminar_campana.html', context)
