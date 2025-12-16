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
    validar_imagen,
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
# Utilidades de usuario y autenticación

def hash_password(password):
    """Envuelve `make_password` de Django para generar un hash seguro."""
    from django.contrib.auth.hashers import make_password
    return make_password(password)


def verificar_password(password, password_hash, usuario=None):
    """Verifica la contraseña contra el hash almacenado.
    Soporta hashes en formato Django (contiene '$') y el hash legacy SHA256.
    Si se detecta una coincidencia legacy y se entrega `usuario`, rehashea
    la contraseña usando el esquema de Django y guarda el usuario.
    """
    import hashlib
    from django.contrib.auth.hashers import check_password as django_check, make_password
    
    if not password or not password_hash:
        return False
    # Si el hash está en formato Django (contiene '$'), usar la verificación estándar
    if '$' in password_hash:
        return django_check(password, password_hash)
    # Fallback: legacy SHA256 hex
    if hashlib.sha256(password.encode()).hexdigest() == password_hash:
        if usuario is not None:
            try:
                usuario.contrasena = make_password(password)
                usuario.save()
            except Exception as e:
                logger.error(f"Error rehasheando contraseña para usuario {usuario.id_usuario}: {e}")
        return True
    return False

def get_usuario_actual(request):
    """Obtiene el usuario actual de la sesión"""
    id_usuario = request.session.get('id_usuario')
    if id_usuario:
        try:
            return Usuario.objects.get(id_usuario=id_usuario)
        except Usuario.DoesNotExist:
            return None
    return None


def puede_actualizar_transaccion(usuario, transaccion, permiso_requerido):
    """Helper para validar si usuario tiene permiso de actualizar transacción.
    
    permiso_requerido puede ser: 'origen', 'destino', 'origen_o_destino', 'representante'
    Retorna tupla: (True/False, mensaje_error o None)
    """
    if permiso_requerido == 'origen':
        if transaccion.user_origen.id != usuario.id_usuario:  # Cambiado: 'user_origen' en lugar de 'id_usuario_origen'
            return False, 'Solo el propietario/vendedor puede realizar esta acción.'
    elif permiso_requerido == 'destino':
        if not transaccion.user_destino or transaccion.user_destino.id != usuario.id_usuario:  # Cambiado: 'user_destino'
            return False, 'Solo el receptor/comprador puede realizar esta acción.'
    elif permiso_requerido == 'origen_o_destino':
        es_origen = transaccion.user_origen.id == usuario.id_usuario
        es_destino = transaccion.user_destino and transaccion.user_destino.id == usuario.id_usuario
        if not (es_origen or es_destino):
            return False, 'No tienes permiso para actualizar esta transacción.'
    elif permiso_requerido == 'representante':
        if not (usuario.es_representante_fundacion() and usuario.fundacion_asignada == transaccion.fundacion):  # Cambiado: 'fundacion'
            return False, 'Solo el representante de la fundación puede realizar esta acción.'
    return True, None


# ==============================================================================
# FUNCIONES HELPER DE PERMISOS Y ROLES
# ==============================================================================

def obtener_permisos_usuario(usuario):
    """Obtiene un diccionario con todos los permisos y roles del usuario.
    
    Retorna dict con:
    - es_cliente: bool
    - es_admin: bool
    - es_moderador: bool
    - es_representante: bool
    - es_staff: bool
    - fundacion_id: int o None
    - puede_gestionar_donaciones: bool
    - puede_ver_reportes: bool
    - puede_moderar_disputas: bool
    """
    if not usuario:
        return {
            'es_cliente': False,
            'es_admin': False,
            'es_moderador': False,
            'es_representante': False,
            'es_staff': False,
            'fundacion_id': None,
            'puede_gestionar_donaciones': False,
            'puede_ver_reportes': False,
            'puede_moderar_disputas': False,
        }
    
    es_admin = usuario.rol == 'ADMINISTRADOR'
    es_moderador = usuario.rol == 'MODERADOR'
    es_representante = usuario.rol == 'REPRESENTANTE_FUNDACION'
    es_cliente = usuario.rol == 'CLIENTE'
    
    return {
        'es_cliente': es_cliente,
        'es_admin': es_admin,
        'es_moderador': es_moderador,
        'es_representante': es_representante,
        'es_staff': usuario.es_staff,
        'fundacion_id': usuario.fundacion_asignada.id_fundacion if es_representante and usuario.fundacion_asignada else None,
        'puede_gestionar_donaciones': es_representante or es_admin,
        'puede_ver_reportes': es_admin or es_moderador,
        'puede_moderar_disputas': es_admin or es_moderador,
    }


def es_propietario_prenda(usuario, prenda):
    """Verifica si el usuario es propietario de la prenda."""
    if not usuario or not prenda:
        return False
    return usuario.id_usuario == getattr(prenda.user, 'id_usuario', None)


def puede_proponer_transaccion(usuario, prenda):
    """Verifica si el usuario puede proponer compra/intercambio de una prenda.
    
    Reglas:
    - No puede ser el propietario
    - La prenda debe estar disponible
    """
    if not usuario or not prenda:
        return False
    if es_propietario_prenda(usuario, prenda):
        return False
    return prenda.esta_disponible()


def puede_donar_prenda(usuario, prenda):
    """Verifica si el usuario puede donar una prenda.
    
    Reglas:
    - Debe ser el propietario
    - La prenda debe estar disponible
    """
    if not usuario or not prenda:
        return False
    if not es_propietario_prenda(usuario, prenda):
        return False
    return prenda.estado == 'DISPONIBLE'


def puede_editar_prenda(usuario, prenda):
    """Verifica si el usuario puede editar una prenda."""
    if not usuario or not prenda:
        return False
    return es_propietario_prenda(usuario, prenda)


def puede_eliminar_prenda(usuario, prenda):
    """Verifica si el usuario puede eliminar una prenda."""
    if not usuario or not prenda:
        return False
    return es_propietario_prenda(usuario, prenda)

# ------------------------------------------------------------------------------------------------------------------
# Vistas Principales

def home(request):
    usuario = get_usuario_actual(request)
    total_prendas = Prenda.objects.count()
    total_usuarios = Usuario.objects.count()
    impacto_total = ImpactoAmbiental.objects.aggregate(
        total_carbono=Sum('carbono_evitar_kg'),
        total_energia=Sum('energia_ahorrada_kwh')
    )
    prendas_recientes = Prenda.objects.select_related('user').order_by('-fecha_publicacion')[:6]  # Cambiado: 'user' en lugar de 'id_usuario'
    context = {
        'usuario': usuario,
        'total_prendas': total_prendas,
        'total_usuarios': total_usuarios,
        'impacto_total': impacto_total,
        'prendas_recientes': prendas_recientes,
    }
    return render(request, 'home.html', context)

@anonymous_required
def registro_usuario(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            usuario = form.save(commit=False)
            usuario.fecha_registro = timezone.now()
            usuario.set_password(form.cleaned_data['contrasena'])
            try:
                usuario.save()
                messages.success(request, f'¡Registro exitoso como {usuario.get_rol_display()}! Ya puedes iniciar sesión.')
                return redirect('login')
            except Exception as e:
                logger.error(f"Error guardando usuario en registro: {e}")
                messages.error(request, 'Error interno. Intenta nuevamente.')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = RegistroForm()
    return render(request, 'auth/registro.html', {'form': form})

@anonymous_required
def login_usuario(request):
    if request.method == 'POST':
        correo = request.POST.get('correo')
        contrasena = request.POST.get('contrasena')
        if not correo or not contrasena:
            messages.error(request, 'Correo y contraseña son obligatorios.')
            return render(request, 'auth/login.html')
        try:
            usuario = Usuario.objects.get(correo=correo)
            if verificar_password(contrasena, usuario.contrasena, usuario):
                request.session['id_usuario'] = usuario.id_usuario  # Cambiado: 'id' en lugar de 'id_usuario'
                messages.success(request, f'¡Bienvenido, {usuario.nombre}!')
                return redirect('home')
            else:
                logger.warning(f"Intento de login fallido para correo: {correo}")
                messages.error(request, 'Usuario o contraseña incorrectos.')
        except Usuario.DoesNotExist:
            logger.warning(f"Intento de login con correo inexistente: {correo}")
            messages.error(request, 'Usuario o contraseña incorrectos.')
    return render(request, 'auth/login.html')

@login_required_custom
def logout_usuario(request):
    request.session.flush()
    response = redirect('home')
    response.delete_cookie('cookie_consent')  # Eliminar cookie de consentimiento al cerrar sesión
    messages.success(request, 'Sesión cerrada correctamente.')
    return response

@login_required_custom
def perfil_usuario(request):
    usuario = get_usuario_actual(request)
    if not usuario:
        return redirect('login')
    if request.method == 'POST':
        form = PerfilForm(request.POST, request.FILES, instance=usuario)
        if form.is_valid():
            if 'imagen_usuario' in request.FILES:
                # Validar imagen antes de guardar
                imagen = request.FILES['imagen_usuario']
                es_valida, mensaje_error = validar_imagen(imagen)
                if not es_valida:
                    messages.error(request, mensaje_error or 'Imagen inválida. Solo JPG/PNG, máximo 5MB.')
                    return render(request, 'auth/perfil.html', {'usuario': usuario, 'form': form})
            try:
                form.save()
                messages.success(request, 'Perfil actualizado correctamente.')
                return redirect('perfil')
            except Exception as e:
                logger.error(f"Error actualizando perfil para usuario {usuario.id_usuario}: {e}")
                messages.error(request, 'Error interno. Intenta nuevamente.')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = PerfilForm(instance=usuario)
    
    total_prendas = Prenda.objects.filter(user=usuario).count()  # Cambiado: 'user' en lugar de 'id_usuario'
    transacciones_realizadas = Transaccion.objects.filter(
        Q(user_origen=usuario) | Q(user_destino=usuario)  # Cambiado: 'user_origen' y 'user_destino'
    ).count()
    impactos = ImpactoAmbiental.objects.select_related('prenda').filter(prenda__user=usuario)  # Cambiado: 'prenda__user'
    impacto_personal = impactos.aggregate(
        total_carbono=Sum('carbono_evitar_kg'),
        total_energia=Sum('energia_ahorrada_kwh')
    )
    context = {
        'usuario': usuario,
        'total_prendas': total_prendas,
        'transacciones_realizadas': transacciones_realizadas,
        'impacto_personal': impacto_personal,
        'form': form,
    }
    return render(request, 'auth/perfil.html', context)

@login_required_custom
def actualizar_foto_perfil(request):
    """Permite al usuario actualizar su foto de perfil."""
    usuario = get_usuario_actual(request)
    if request.method == 'POST' and 'imagen_usuario' in request.FILES:
        # Validar imagen antes de guardar
        imagen = request.FILES['imagen_usuario']
        es_valida, mensaje_error = validar_imagen(imagen)
        if not es_valida:
            messages.error(request, mensaje_error or 'Imagen inválida. Solo JPG/PNG, máximo 5MB.')
            return redirect('perfil')

        usuario.imagen_usuario = imagen
        usuario.save()
        messages.success(request, 'Foto de perfil actualizada.')
        return redirect('perfil')
    messages.error(request, 'Sube una imagen válida.')
    return redirect('perfil')

@login_required_custom
def actualizar_imagen_prenda(request, id_prenda):
    """Actualiza la imagen de una prenda del usuario."""
    usuario = get_usuario_actual(request)
    prenda = get_object_or_404(Prenda, id_prenda=id_prenda, user=usuario)
    if request.method == 'POST' and 'imagen_prenda' in request.FILES:
        prenda.imagen_prenda = request.FILES['imagen_prenda']
        prenda.save()
        messages.success(request, 'Imagen de prenda actualizada.')
        return redirect('detalle_prenda', id_prenda=getattr(prenda, 'id_prenda', getattr(prenda, 'id', prenda.pk)))
    messages.error(request, 'Sube una imagen válida.')
    return redirect('editar_prenda', id_prenda=getattr(prenda, 'id_prenda', getattr(prenda, 'id', prenda.pk)))

@login_required_custom
def actualizar_logo_fundacion(request, id_fundacion):
    """Actualiza el logo de la fundación. Solo para representantes."""
    usuario = get_usuario_actual(request)
    fundacion = get_object_or_404(Fundacion, id_fundacion=id_fundacion, representante=usuario)
    if request.method == 'POST' and 'imagen_fundacion' in request.FILES:
        fundacion.imagen_fundacion = request.FILES['imagen_fundacion']
        fundacion.save()
        messages.success(request, 'Logo de fundación actualizado.')
        return redirect('panel_fundacion')
    messages.error(request, 'Sube una imagen válida.')
    return redirect('panel_fundacion')

@login_required_custom
def session_info(request):
    """Muestra información relevante de la sesión actual"""
    usuario = get_usuario_actual(request)
    from datetime import datetime

    # Recuperar/asegurar nombre y correo en sesión
    id_usuario = request.session.get('id_usuario')
    usuario_nombre = request.session.get('usuario_nombre')
    usuario_correo = request.session.get('usuario_correo')

    if (not usuario_nombre or not usuario_correo) and id_usuario:
        try:
            u = Usuario.objects.only('nombre', 'correo').get(id_usuario=id_usuario)
            usuario_nombre = u.nombre
            usuario_correo = u.correo
            request.session['usuario_nombre'] = usuario_nombre
            request.session['usuario_correo'] = usuario_correo
        except Usuario.DoesNotExist:
            logger.warning(f"Usuario con ID {id_usuario} no encontrado en session_info")
            usuario_nombre = None
            usuario_correo = None

    # Información de la sesión
    session_data = {
        'session_key': (request.session.session_key or '')[:10] + '...' if request.session.session_key else 'N/A',  # Limitado para seguridad
        'id_usuario': id_usuario,
        'usuario_nombre': usuario_nombre,
        'usuario_correo': usuario_correo,
    }

    # Timestamp de login
    login_timestamp = request.session.get('login_timestamp')
    if login_timestamp:
        try:
            login_dt = datetime.fromisoformat(login_timestamp)
            session_data['login_timestamp'] = login_dt.strftime('%d/%m/%Y %H:%M:%S')
            session_data['tiempo_sesion'] = str(timezone.now() - login_dt)
        except ValueError:
            logger.error(f"Error parseando login_timestamp: {login_timestamp}")
            session_data['login_timestamp'] = 'Error'

    # Última actividad
    ultima_actividad = request.session.get('ultima_actividad')
    if ultima_actividad:
        try:
            ultima_dt = datetime.fromisoformat(ultima_actividad)
            session_data['ultima_actividad'] = ultima_dt.strftime('%d/%m/%Y %H:%M:%S')
            tiempo_inactivo = (timezone.now() - ultima_dt).total_seconds()
            session_data['tiempo_inactivo'] = f"{int(tiempo_inactivo)} segundos"
        except ValueError:
            logger.error(f"Error parseando ultima_actividad: {ultima_actividad}")
            session_data['ultima_actividad'] = 'Error'

    # Expiración de la sesión
    expiry = request.session.get_expiry_age()
    if expiry:
        session_data['expira_en'] = f"{int(expiry / 60)} minutos"

    # Contador de requests opcional
    session_data['request_counter'] = request.session.get('request_counter', 0)

    context = {
        'usuario': usuario,
        'session_data': session_data,
    }

    return render(request, 'auth/session_info.html', context)


@ajax_login_required
def session_status(request):
    """Endpoint AJAX para verificar estado de sesión"""
    from datetime import datetime

    ultima_actividad = request.session.get('ultima_actividad')
    tiempo_restante = None
    if ultima_actividad:
        try:
            ultima_dt = datetime.fromisoformat(ultima_actividad)
            tiempo_inactivo = (timezone.now() - ultima_dt).total_seconds()
            tiempo_restante = max(0, 1800 - int(tiempo_inactivo))  # 1800 segundos = 30 minutos
        except ValueError:
            logger.error(f"Error parseando ultima_actividad en session_status: {ultima_actividad}")

    # Asegurar nombre desde DB si no está en la sesión
    id_usuario = request.session.get('id_usuario')
    usuario_nombre = request.session.get('usuario_nombre')
    if (not usuario_nombre) and id_usuario:
        try:
            u = Usuario.objects.only('nombre').get(id_usuario=id_usuario)
            usuario_nombre = u.nombre
            request.session['usuario_nombre'] = usuario_nombre
        except Usuario.DoesNotExist:
            logger.warning(f"Usuario con ID {id_usuario} no encontrado en session_status")
            usuario_nombre = None

    return JsonResponse({
        'autenticado': True,
        'id_usuario': id_usuario,
        'usuario_nombre': usuario_nombre,
        'tiempo_restante': tiempo_restante,
        'session_key': (request.session.session_key or '')[:10] + '...' if request.session.session_key else 'N/A'  # Limitado para seguridad
    })


@login_required_custom
def renovar_sesion(request):
    """Renueva la sesión y actualiza el timestamp de última actividad"""
    if request.method == 'POST':
        try:
            request.session['ultima_actividad'] = timezone.now().isoformat()
            request.session.modified = True
            if not request.session.get('login_timestamp'):
                request.session['login_timestamp'] = timezone.now().isoformat()
            return JsonResponse({
                'success': True,
                'message': 'Sesión renovada',
                'nueva_expiracion': request.session.get_expiry_age()
            })
        except Exception as e:
            logger.error(f"Error renovando sesión para usuario {request.session.get('id_usuario')}: {e}")
            return JsonResponse({'error': 'Error interno'}, status=500)
    return JsonResponse({'error': 'Método no permitido'}, status=405)