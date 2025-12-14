from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.utils import timezone
from django.http import JsonResponse
from django import forms  # Agregado para forms
import hashlib
import json
import logging  # Agregado para logging
#xdxdxd
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
# Mensajería entre usuarios

@login_required_custom
def lista_mensajes(request):
    """Vista de la lista de conversaciones del usuario."""
    usuario = get_usuario_actual(request)
    # Usuarios con los que hay intercambio de mensajes
    enviados = Mensaje.objects.filter(emisor=usuario).values_list('receptor', flat=True)  # Cambiado: 'emisor', 'receptor'
    recibidos = Mensaje.objects.filter(receptor=usuario).values_list('emisor', flat=True)  # Cambiado: 'receptor', 'emisor'
    ids_conversaciones = set([id for id in list(enviados) + list(recibidos) if id is not None])
    conversaciones = Usuario.objects.filter(id_usuario__in=ids_conversaciones)
    context = {
        'usuario': usuario,
        'conversaciones': conversaciones,
    }
    return render(request, 'mensajes/lista_mensajes.html', context)

@login_required_custom
def conversacion(request, id_usuario):
    """Muestra la conversación entre el usuario y otro usuario específico."""
    usuario = get_usuario_actual(request)
    otro_usuario = get_object_or_404(Usuario, pk=id_usuario)  # Cambiado: 'pk=id_usuario'
    # Mensajes entre ambos (enviado/recibido)
    mensajes_conversacion = Mensaje.objects.filter(
        Q(emisor=usuario, receptor=otro_usuario) |  # Cambiado: 'emisor', 'receptor'
        Q(emisor=otro_usuario, receptor=usuario)
    ).order_by('fecha_envio').select_related('emisor', 'receptor')  # Agregado select_related
    context = {
        'usuario': usuario,
        'otro_usuario': otro_usuario,
        'mensajes': mensajes_conversacion,
    }
    return render(request, 'mensajes/conversacion.html', context)

@login_required_custom
def enviar_mensaje(request):
    """Envía un mensaje de usuario a usuario (AJAX o POST normal)."""
    usuario = get_usuario_actual(request)
    if request.method == 'POST':
        receptor_id = request.POST.get('receptor_id')
        contenido = request.POST.get('contenido')
        if not receptor_id or not contenido or len(contenido.strip()) < 2:
            return JsonResponse({'error': 'Datos incompletos.'}, status=400)
        try:
            receptor = Usuario.objects.get(pk=receptor_id)  # Cambiado: 'pk=receptor_id'
            Mensaje.objects.create(
                emisor=usuario,  # Cambiado: 'emisor'
                receptor=receptor,  # Cambiado: 'receptor'
                contenido=contenido.strip(),
                fecha_envio=timezone.now()
            )
            messages.success(request, f'Mensaje enviado a {receptor.nombre}')
            # Si usas AJAX:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            return redirect('conversacion', id_usuario=receptor.pk)  # Cambiado: 'receptor.pk'
        except Usuario.DoesNotExist:
            return JsonResponse({'error': 'Receptor no encontrado.'}, status=404)
        except Exception as e:
            logger.error(f"Error enviando mensaje de {usuario.id_usuario} a {receptor_id}: {e}")
            return JsonResponse({'error': 'Error interno.'}, status=500)
    return JsonResponse({'error': 'Método no permitido'}, status=405)