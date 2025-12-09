# Guía de Correcciones - APIs EcoPrenda

## 1. Crear archivo `.env` (NO COMMITEAR A GIT)

```bash
# .env
# ==================== GEOAPIFY ====================
GEOAPIFY_API_KEY=tu_nueva_clave_aqui

# ==================== CLOUDINARY ====================
CLOUDINARY_CLOUD_NAME=tu_cloud_name
CLOUDINARY_API_KEY=tu_api_key
CLOUDINARY_API_SECRET=tu_api_secret

# ==================== CLARIFAI ====================
CLARIFAI_PAT=tu_nuevo_pat_token
```

## 2. Crear `.env.example` (SÍ COMMITEAR A GIT)

```bash
# .env.example - Copiar a .env y llenar con valores reales
GEOAPIFY_API_KEY=
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=
CLARIFAI_PAT=
```

## 3. Agregar a `.gitignore`

```
# Archivos de ambiente (NO COMMITEAR)
.env
.env.local
.env.*.local

# Credenciales
credentials.json
secrets.json
```

## 4. Actualizar `requirements.txt`

**ANTES:**
```txt
cloudinary==1.44.1
...
cloudinary==1.41.0  # ← DUPLICADO
clarifai-grpc==10.0.9
```

**DESPUÉS:**
```txt
django==5.2.5
djangorestframework==3.16.1
pillow==11.3.0
psycopg2-binary==2.9.11
python-dotenv==1.2.1
dj-database-url==3.0.1
requests==2.32.4
cryptography==46.0.3

# ==================== CLOUDINARY ====================
django-cloudinary-storage==0.3.0
cloudinary==1.44.1  # ← Versión más reciente

# ==================== CLARIFAI ====================
clarifai-grpc==10.0.9

# ==================================================
# Instalar con: pip install -r requirements.txt
# ==================================================
```

## 5. Actualizar `settings.py`

**PROBLEMA ACTUAL (líneas 212-242):**
```python
# ⚠️ INSEGURO - Credenciales hardcodeadas
GEOAPIFY_API_KEY = os.environ.get('GEOAPIFY_API_KEY', '2346b3fc49854fc9bd0017b7fa0647ca')

CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME', 'daev2fgjt'),
    'API_KEY': os.environ.get('CLOUDINARY_API_KEY', '176413229185279'),
    'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET', 'oCui-XzSjheafkQKxb4s_QmQ0W8')
}

CLARIFAI_PAT = os.environ.get('CLARIFAI_PAT', '05b8547c887c494ba23a1c4a611c5036')
```

**SOLUCIÓN (REEMPLAZAR):**
```python
import os
from django.core.exceptions import ImproperlyConfigured

# ====================== GEOAPIFY (Mapas) ======================
GEOAPIFY_API_KEY = os.environ.get('GEOAPIFY_API_KEY')
if not GEOAPIFY_API_KEY and not DEBUG:
    raise ImproperlyConfigured('GEOAPIFY_API_KEY no está configurada')

# ====================== CLOUDINARY (Imágenes) ======================
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME'),
    'API_KEY': os.environ.get('CLOUDINARY_API_KEY'),
    'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET')
}

# Validar credenciales en producción
if not DEBUG:
    for key, value in CLOUDINARY_STORAGE.items():
        if not value:
            raise ImproperlyConfigured(f'CLOUDINARY_{key} no está configurada')

DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# Configuración adicional de Cloudinary
import cloudinary
import cloudinary.uploader
import cloudinary.api

cloudinary.config(
    cloud_name=CLOUDINARY_STORAGE['CLOUD_NAME'],
    api_key=CLOUDINARY_STORAGE['API_KEY'],
    api_secret=CLOUDINARY_STORAGE['API_SECRET'],
    secure=True
)

# ====================== CLARIFAI (Detección) ======================
CLARIFAI_PAT = os.environ.get('CLARIFAI_PAT')
if not CLARIFAI_PAT and not DEBUG:
    raise ImproperlyConfigured('CLARIFAI_PAT no está configurada')

CLARIFAI_USER_ID = 'clarifai'
CLARIFAI_APP_ID = 'main'
CLARIFAI_MODEL_ID = 'apparel-detection'
CLARIFAI_MODEL_VERSION_ID = '1ed35c3d176f45d69d2aa7971e6ab9fe'
```

## 6. Mejorar `cloudinary_utils.py` (Agregar validaciones)

**Agregar al inicio del archivo:**
```python
import logging

logger = logging.getLogger(__name__)

class CloudinaryError(Exception):
    """Error personalizado para Cloudinary"""
    pass
```

**Mejorar `subir_imagen_cloudinary()`:**
```python
def subir_imagen_cloudinary(imagen, carpeta='ecoprenda', public_id=None, transformaciones=None):
    """Sube una imagen a Cloudinary con opciones de transformación."""
    
    if not imagen:
        logger.error("Intento de subir imagen vacía")
        raise CloudinaryError("No se proporcionó imagen")
    
    try:
        opciones = {
            'folder': carpeta,
            'resource_type': 'image',
            'quality': 'auto:good',
            'fetch_format': 'auto',
        }
        
        if public_id:
            opciones['public_id'] = public_id
            opciones['overwrite'] = True
        
        if transformaciones:
            opciones['transformation'] = transformaciones
        
        resultado = cloudinary.uploader.upload(imagen, **opciones)
        
        # Validar respuesta
        if resultado.get('error'):
            logger.error(f"Error Cloudinary: {resultado['error']}")
            raise CloudinaryError(f"Error al subir: {resultado['error']}")
        
        logger.info(f"Imagen subida exitosamente: {resultado.get('public_id')}")
        return resultado
    
    except cloudinary.exceptions.Error as e:
        logger.error(f"Error Cloudinary: {str(e)}")
        raise CloudinaryError(f"Error al subir imagen: {str(e)}")
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}")
        raise
```

## 7. Mejorar `clarifai_utils.py` (Agregar retry y logging)

**Agregar al inicio:**
```python
import logging
from time import sleep

logger = logging.getLogger(__name__)

class ClarifaiError(Exception):
    """Error personalizado para Clarifai"""
    pass

# Configuración de reintentos
MAX_RETRIES = 3
RETRY_DELAY = 1  # segundos
```

**Mejorar `detectar_prendas_imagen()`:**
```python
def detectar_prendas_imagen(imagen_url=None, imagen_bytes=None, retries=0):
    """Detecta y clasifica prendas en una imagen usando Clarifai."""
    
    if not imagen_url and not imagen_bytes:
        logger.warning("Ninguna imagen proporcionada")
        return []
    
    try:
        channel = ClarifaiChannel.get_grpc_channel()
        stub = service_pb2_grpc.V2Stub(channel)
        
        metadata = (('authorization', 'Key ' + settings.CLARIFAI_PAT),)
        
        user_data_object = resources_pb2.UserAppIDSet(
            user_id=settings.CLARIFAI_USER_ID,
            app_id=settings.CLARIFAI_APP_ID
        )
        
        if imagen_url:
            image_input = resources_pb2.Image(url=imagen_url)
        else:
            image_input = resources_pb2.Image(base64=imagen_bytes)
        
        response = stub.PostModelOutputs(
            service_pb2.PostModelOutputsRequest(
                user_app_id=user_data_object,
                model_id=settings.CLARIFAI_MODEL_ID,
                version_id=settings.CLARIFAI_MODEL_VERSION_ID,
                inputs=[resources_pb2.Input(data=resources_pb2.Data(image=image_input))]
            ),
            metadata=metadata
        )
        
        if response.status.code != status_code_pb2.SUCCESS:
            error_msg = response.status.description
            logger.error(f"Clarifai error: {error_msg}")
            
            # Reintentar si es error temporal
            if retries < MAX_RETRIES:
                logger.info(f"Reintentando... ({retries + 1}/{MAX_RETRIES})")
                sleep(RETRY_DELAY)
                return detectar_prendas_imagen(imagen_url, imagen_bytes, retries + 1)
            
            raise ClarifaiError(f"Error Clarifai: {error_msg}")
        
        prendas_detectadas = []
        regions = response.outputs[0].data.regions
        
        for region in regions:
            bbox = {
                'top': round(region.region_info.bounding_box.top_row, 3),
                'left': round(region.region_info.bounding_box.left_col, 3),
                'bottom': round(region.region_info.bounding_box.bottom_row, 3),
                'right': round(region.region_info.bounding_box.right_col, 3)
            }
            
            for concept in region.data.concepts:
                prenda = {
                    'nombre': concept.name,
                    'confianza': round(concept.value, 4),
                    'bbox': bbox
                }
                prendas_detectadas.append(prenda)
        
        logger.info(f"Detectadas {len(prendas_detectadas)} prendas")
        return prendas_detectadas
    
    except ClarifaiError:
        raise
    except Exception as e:
        logger.error(f"Error inesperado en Clarifai: {str(e)}")
        return []
```

## 8. Configurar logging en `settings.py`

**Agregar:**
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'ecoprenda.log'),
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'App.cloudinary_utils': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
        },
        'App.clarifai_utils': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
        },
    },
}
```

## 9. Pruebas de Configuración

**Crear `test_apis.py` en el directorio Proyecto:**
```python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Proyecto.settings')
django.setup()

from django.conf import settings

def verificar_apis():
    """Verifica que todas las APIs estén configuradas"""
    
    print("🔍 Verificando configuración de APIs...")
    print()
    
    # Geoapify
    print("1️⃣  GEOAPIFY")
    if settings.GEOAPIFY_API_KEY:
        print("   ✅ GEOAPIFY_API_KEY configurada")
    else:
        print("   ❌ GEOAPIFY_API_KEY NO configurada")
    print()
    
    # Cloudinary
    print("2️⃣  CLOUDINARY")
    reqs = ['CLOUD_NAME', 'API_KEY', 'API_SECRET']
    for req in reqs:
        val = settings.CLOUDINARY_STORAGE.get(req)
        if val:
            print(f"   ✅ {req} configurada")
        else:
            print(f"   ❌ {req} NO configurada")
    print()
    
    # Clarifai
    print("3️⃣  CLARIFAI")
    if settings.CLARIFAI_PAT:
        print("   ✅ CLARIFAI_PAT configurada")
    else:
        print("   ❌ CLARIFAI_PAT NO configurada")
    print()
    
    print("✅ Verificación completada")

if __name__ == '__main__':
    verificar_apis()
```

**Ejecutar:**
```bash
python test_apis.py
```

## 10. Checklist Final

- [ ] Crear `.env` con credenciales reales
- [ ] Crear `.env.example` para documentación
- [ ] Actualizar `.gitignore`
- [ ] Eliminar valores por defecto de settings.py
- [ ] Agregar validaciones de credenciales
- [ ] Actualizar requirements.txt (sin duplicados)
- [ ] Agregar logging estructurado
- [ ] Mejorar manejo de errores
- [ ] Implementar retry logic
- [ ] Ejecutar test_apis.py
- [ ] Probar cada API en desarrollo
- [ ] Documentar en README cómo configurar

