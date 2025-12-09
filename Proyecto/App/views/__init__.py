# Importar todas las funciones de los módulos de vistas

from .cookie import (
    configurar_cookies,
    aceptar_cookies,
    rechazar_cookies,
    obtener_preferencias_cookies,
    eliminar_cookies,
)

from .auth import (
    hash_password,
    verificar_password,
    get_usuario_actual,
    puede_actualizar_transaccion,
    home,
    registro_usuario,
    login_usuario,
    logout_usuario,
    perfil_usuario,
    actualizar_foto_perfil,
    actualizar_imagen_prenda,
    actualizar_logo_fundacion,
    session_info,
    session_status,
    renovar_sesion,
)

from .prenda import (
    lista_prendas,
    detalle_prenda,
    crear_prenda,
    editar_prenda,
    eliminar_prenda,
    mis_prendas,
    buscar_prendas,
)

from .transaccion import (
    proponer_intercambio,
    marcar_intercambio_entregado,
    confirmar_recepcion_intercambio,
    cancelar_intercambio,
    comprar_prenda,
    marcar_compra_entregado,
    marcar_donacion_enviada,
    confirmar_recepcion_compra,
    cancelar_compra,
    donar_prenda,
    mis_transacciones,
    actualizar_estado_transaccion,
    reportar_disputa,
    resolver_disputa,
)

from .mensaje import (
    lista_mensajes,
    conversacion,
    enviar_mensaje,
)

from .fundacion import (
    lista_fundaciones,
    detalle_fundacion,
    panel_fundacion,
    gestionar_donaciones,
    confirmar_recepcion_donacion,
    enviar_mensaje_agradecimiento,
    estadisticas_donaciones,
    mapa_fundaciones,
    actualizar_ubicacion_usuario,
    actualizar_ubicacion_fundacion,
)

from .logro import (
    verificar_logros,
    desbloquear_logro,
    mis_logros,
)

from .impacto_ambiental import (
    panel_impacto,
    mi_impacto,
)

from .campana import (
    crear_campana,
    campanas_solidarias,
    detalle_campana,
    donar_a_campana,
    mis_campanas,
)

from .api_y_galeria import (
    galeria_imagenes,
    informe_impacto,
    comparador_impacto,
    api_calcular_impacto,
    api_sugerir_categoria,
)

__all__ = [
    'configurar_cookies',
    'aceptar_cookies',
    'rechazar_cookies',
    'obtener_preferencias_cookies',
    'eliminar_cookies',
    'hash_password',
    'verificar_password',
    'get_usuario_actual',
    'puede_actualizar_transaccion',
    'home',
    'registro_usuario',
    'login_usuario',
    'logout_usuario',
    'perfil_usuario',
    'actualizar_foto_perfil',
    'actualizar_imagen_prenda',
    'actualizar_logo_fundacion',
    'session_info',
    'session_status',
    'renovar_sesion',
    'lista_prendas',
    'detalle_prenda',
    'crear_prenda',
    'editar_prenda',
    'eliminar_prenda',
    'mis_prendas',
    'buscar_prendas',
    'proponer_intercambio',
    'marcar_intercambio_entregado',
    'confirmar_recepcion_intercambio',
    'cancelar_intercambio',
    'comprar_prenda',
    'marcar_compra_entregado',
    'marcar_donacion_enviada',
    'confirmar_recepcion_compra',
    'cancelar_compra',
    'donar_prenda',
    'mis_transacciones',
    'actualizar_estado_transaccion',
    'reportar_disputa',
    'resolver_disputa',
    'lista_mensajes',
    'conversacion',
    'enviar_mensaje',
    'lista_fundaciones',
    'detalle_fundacion',
    'panel_fundacion',
    'gestionar_donaciones',
    'confirmar_recepcion_donacion',
    'enviar_mensaje_agradecimiento',
    'estadisticas_donaciones',
    'mapa_fundaciones',
    'actualizar_ubicacion_usuario',
    'actualizar_ubicacion_fundacion',
    'verificar_logros',
    'desbloquear_logro',
    'mis_logros',
    'panel_impacto',
    'mi_impacto',
    'crear_campana',
    'campanas_solidarias',
    'detalle_campana',
    'donar_a_campana',
    'mis_campanas',
    'galeria_imagenes',
    'informe_impacto',
    'comparador_impacto',
    'api_calcular_impacto',
    'api_sugerir_categoria',
]
