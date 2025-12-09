"""
Utilidades para detección de prendas con Clarifai API
Usa el modelo apparel-detection para identificar y clasificar prendas automáticamente
"""

import logging
from time import sleep
from django.conf import settings
from clarifai_grpc.channel.clarifai_channel import ClarifaiChannel
from clarifai_grpc.grpc.api import resources_pb2, service_pb2, service_pb2_grpc
from clarifai_grpc.grpc.api.status import status_code_pb2

# Configurar logger
logger = logging.getLogger(__name__)

# Configuración de reintentos
MAX_RETRIES = 3
RETRY_DELAY = 1  # segundos


class ClarifaiError(Exception):
    """Error personalizado para Clarifai"""
    pass


def detectar_prendas_imagen(imagen_url=None, imagen_bytes=None, retries=0):
    """
    Detecta y clasifica prendas en una imagen usando Clarifai.
    
    Args:
        imagen_url: URL de la imagen (usar para imágenes ya subidas a Cloudinary)
        imagen_bytes: Bytes de la imagen (usar para imágenes locales antes de subir)
        retries: Número de reintentos internos (no llamar directamente)
    
    Returns:
        list: Lista de prendas detectadas con sus características
        [
            {
                'nombre': 'shirt',
                'confianza': 0.98,
                'bbox': {'top': 0.123, 'left': 0.234, 'bottom': 0.456, 'right': 0.567}
            },
            ...
        ]
    
    Raises:
        ClarifaiError: Si hay error después de reintentos
    
    Ejemplo:
        # Desde URL (después de subir a Cloudinary)
        prendas = detectar_prendas_imagen(imagen_url='https://res.cloudinary.com/...')
        
        # Desde bytes (antes de subir)
        with open('prenda.jpg', 'rb') as f:
            prendas = detectar_prendas_imagen(imagen_bytes=f.read())
    """
    
    if not imagen_url and not imagen_bytes:
        logger.warning("Ninguna imagen proporcionada para detección")
        return []
    
    try:
        # Configurar canal y stub
        channel = ClarifaiChannel.get_grpc_channel()
        stub = service_pb2_grpc.V2Stub(channel)
        
        # Metadata con autenticación
        metadata = (('authorization', 'Key ' + settings.CLARIFAI_PAT),)
        
        # User App ID
        user_data_object = resources_pb2.UserAppIDSet(
            user_id=settings.CLARIFAI_USER_ID,
            app_id=settings.CLARIFAI_APP_ID
        )
        
        # Preparar input según el tipo
        if imagen_url:
            image_input = resources_pb2.Image(url=imagen_url)
            logger.debug(f"🔍 Detectando prendas desde URL")
        else:
            image_input = resources_pb2.Image(base64=imagen_bytes)
            logger.debug(f"🔍 Detectando prendas desde bytes")
        
        # Hacer request a Clarifai
        response = stub.PostModelOutputs(
            service_pb2.PostModelOutputsRequest(
                user_app_id=user_data_object,
                model_id=settings.CLARIFAI_MODEL_ID,
                version_id=settings.CLARIFAI_MODEL_VERSION_ID,
                inputs=[
                    resources_pb2.Input(
                        data=resources_pb2.Data(image=image_input)
                    )
                ]
            ),
            metadata=metadata
        )
        
        # Verificar respuesta
        if response.status.code != status_code_pb2.SUCCESS:
            error_msg = response.status.description
            logger.error(f"❌ Error Clarifai: {error_msg}")
            
            # Reintentar si es error temporal
            if retries < MAX_RETRIES:
                logger.info(f"⚠️ Reintentando... ({retries + 1}/{MAX_RETRIES})")
                sleep(RETRY_DELAY)
                return detectar_prendas_imagen(imagen_url, imagen_bytes, retries + 1)
            
            raise ClarifaiError(f"Error Clarifai después de {MAX_RETRIES} reintentos: {error_msg}")
        
        # Procesar resultados
        prendas_detectadas = []
        regions = response.outputs[0].data.regions
        
        for region in regions:
            # Extraer bounding box
            bbox = {
                'top': round(region.region_info.bounding_box.top_row, 3),
                'left': round(region.region_info.bounding_box.left_col, 3),
                'bottom': round(region.region_info.bounding_box.bottom_row, 3),
                'right': round(region.region_info.bounding_box.right_col, 3)
            }
            
            # Extraer conceptos (tipos de prenda)
            for concept in region.data.concepts:
                prenda = {
                    'nombre': concept.name,
                    'confianza': round(concept.value, 4),
                    'bbox': bbox
                }
                prendas_detectadas.append(prenda)
        
        logger.info(f"✅ Detectadas {len(prendas_detectadas)} prendas")
        return prendas_detectadas
    
    except ClarifaiError:
        raise
    except Exception as e:
        logger.error(f"❌ Error inesperado en Clarifai: {str(e)}")
        return []


def mapear_categoria_clarifai(nombre_clarifai):
    """
    Mapea el nombre detectado por Clarifai a las categorías de EcoPrenda.
    
    Args:
        nombre_clarifai: Nombre detectado por Clarifai (ej: 'shirt', 'pants', etc.)
    
    Returns:
        str: Categoría de EcoPrenda
    
    Mapeo de términos:
        Clarifai → EcoPrenda
        shirt, t-shirt, blouse → Camiseta
        pants, jeans, trousers → Pantalón
        dress, gown → Vestido
        jacket, coat, blazer → Chaqueta
        shoes, sneakers, boots → Zapatos
        bag, hat, scarf, belt → Accesorios
    """
    
    mapeo = {
        # Camisetas
        'shirt': 'Camiseta',
        't-shirt': 'Camiseta',
        'blouse': 'Camiseta',
        'top': 'Camiseta',
        'polo': 'Camiseta',
        
        # Pantalones
        'pants': 'Pantalón',
        'jeans': 'Pantalón',
        'trousers': 'Pantalón',
        'shorts': 'Pantalón',
        'leggings': 'Pantalón',
        
        # Vestidos
        'dress': 'Vestido',
        'gown': 'Vestido',
        'skirt': 'Vestido',
        
        # Chaquetas
        'jacket': 'Chaqueta',
        'coat': 'Chaqueta',
        'blazer': 'Chaqueta',
        'sweater': 'Chaqueta',
        'hoodie': 'Chaqueta',
        'cardigan': 'Chaqueta',
        
        # Zapatos
        'shoes': 'Zapatos',
        'sneakers': 'Zapatos',
        'boots': 'Zapatos',
        'sandals': 'Zapatos',
        'heels': 'Zapatos',
        
        # Accesorios
        'bag': 'Accesorios',
        'purse': 'Accesorios',
        'backpack': 'Accesorios',
        'hat': 'Accesorios',
        'cap': 'Accesorios',
        'scarf': 'Accesorios',
        'belt': 'Accesorios',
        'tie': 'Accesorios',
        'gloves': 'Accesorios',
        'sunglasses': 'Accesorios',
    }
    
    nombre_lower = nombre_clarifai.lower()
    return mapeo.get(nombre_lower, 'Accesorios')  # Default: Accesorios


def sugerir_categoria_automatica(imagen_url=None, imagen_bytes=None, umbral_confianza=0.7):
    """
    Sugiere automáticamente la categoría de una prenda basándose en la detección.
    
    Args:
        imagen_url: URL de la imagen
        imagen_bytes: Bytes de la imagen
        umbral_confianza: Confianza mínima para aceptar sugerencia (0.0 - 1.0)
    
    Returns:
        dict: {
            'categoria_sugerida': str,
            'confianza': float,
            'prendas_detectadas': list,
            'mensaje': str
        }
    
    Ejemplo:
        resultado = sugerir_categoria_automatica(imagen_url='https://...')
        if resultado['confianza'] >= 0.7:
            prenda.categoria = resultado['categoria_sugerida']
    """
    
    prendas = detectar_prendas_imagen(imagen_url, imagen_bytes)
    
    if not prendas:
        return {
            'categoria_sugerida': None,
            'confianza': 0.0,
            'prendas_detectadas': [],
            'mensaje': 'No se detectaron prendas en la imagen.'
        }
    
    # Ordenar por confianza (mayor a menor)
    prendas_ordenadas = sorted(prendas, key=lambda x: x['confianza'], reverse=True)
    prenda_principal = prendas_ordenadas[0]
    
    # Mapear a categoría de EcoPrenda
    categoria = mapear_categoria_clarifai(prenda_principal['nombre'])
    confianza = prenda_principal['confianza']
    
    # Generar mensaje
    if confianza >= umbral_confianza:
        mensaje = f"Se detectó '{prenda_principal['nombre']}' con {confianza*100:.1f}% de confianza."
    else:
        mensaje = f"Baja confianza ({confianza*100:.1f}%). Verifica la categoría manualmente."
    
    return {
        'categoria_sugerida': categoria,
        'confianza': confianza,
        'prendas_detectadas': prendas,
        'mensaje': mensaje
    }


def obtener_descripcion_automatica(prendas_detectadas):
    """
    Genera una descripción automática basada en las prendas detectadas.
    
    Args:
        prendas_detectadas: Lista de prendas detectadas por Clarifai
    
    Returns:
        str: Descripción generada automáticamente
    
    Ejemplo:
        descripcion = obtener_descripcion_automatica(prendas)
        # "Imagen contiene: shirt (98%), jeans (95%), shoes (87%)"
    """
    
    if not prendas_detectadas:
        return ""
    
    # Tomar solo las 3 más confiables
    top_prendas = sorted(prendas_detectadas, key=lambda x: x['confianza'], reverse=True)[:3]
    
    items = []
    for prenda in top_prendas:
        nombre = prenda['nombre']
        confianza_pct = prenda['confianza'] * 100
        items.append(f"{nombre} ({confianza_pct:.0f}%)")
    
    return "Detectado: " + ", ".join(items)


def validar_imagen_es_prenda(imagen_url=None, imagen_bytes=None, umbral=0.5):
    """
    Valida que la imagen contenga al menos una prenda de vestir.
    Útil para rechazar imágenes que no sean prendas.
    
    Args:
        imagen_url: URL de la imagen
        imagen_bytes: Bytes de la imagen
        umbral: Confianza mínima para considerar válida (default: 0.5)
    
    Returns:
        tuple: (es_valida: bool, mensaje: str)
    
    Ejemplo:
        es_valida, mensaje = validar_imagen_es_prenda(imagen_url='https://...')
        if not es_valida:
            return error_response(mensaje)
    """
    
    prendas = detectar_prendas_imagen(imagen_url, imagen_bytes)
    
    if not prendas:
        return False, "No se detectó ninguna prenda en la imagen. Por favor, sube una imagen clara de la prenda."
    
    # Verificar si al menos una prenda supera el umbral
    prenda_valida = any(p['confianza'] >= umbral for p in prendas)
    
    if not prenda_valida:
        return False, f"La imagen no parece contener una prenda clara. Confianza máxima: {max(p['confianza'] for p in prendas)*100:.0f}%"
    
    return True, "Imagen válida"


def analizar_imagen_completa(imagen_url=None, imagen_bytes=None):
    """
    Análisis completo de una imagen: detección, categorización, validación.
    
    Args:
        imagen_url: URL de la imagen
        imagen_bytes: Bytes de la imagen
    
    Returns:
        dict: Análisis completo con toda la información
    
    Ejemplo:
        analisis = analizar_imagen_completa(imagen_url='https://...')
        print(analisis['resumen'])
    """
    
    prendas = detectar_prendas_imagen(imagen_url, imagen_bytes)
    sugerencia = sugerir_categoria_automatica(imagen_url, imagen_bytes)
    es_valida, mensaje_validacion = validar_imagen_es_prenda(imagen_url, imagen_bytes)
    descripcion = obtener_descripcion_automatica(prendas)
    
    return {
        'es_valida': es_valida,
        'mensaje_validacion': mensaje_validacion,
        'categoria_sugerida': sugerencia['categoria_sugerida'],
        'confianza': sugerencia['confianza'],
        'descripcion_auto': descripcion,
        'total_prendas_detectadas': len(prendas),
        'prendas_detalle': prendas,
        'resumen': f"Detectadas {len(prendas)} prenda(s). Sugerencia: {sugerencia['categoria_sugerida']} ({sugerencia['confianza']*100:.1f}%)"
    }


# ==============================================================================
# CONSTANTES
# ==============================================================================

CATEGORIAS_ECOPRENDA = [
    'Camiseta',
    'Pantalón',
    'Vestido',
    'Chaqueta',
    'Zapatos',
    'Accesorios'
]

UMBRAL_CONFIANZA_RECOMENDADO = 0.70  # 70% de confianza mínima
UMBRAL_VALIDACION_MINIMA = 0.50      # 50% para considerar que es una prenda