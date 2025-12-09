# 🔍 Verificación de Configuración de APIs - EcoPrenda

**Fecha de Verificación:** 9 de Diciembre 2025

---

## 📋 Resumen Ejecutivo

Se ha verificado el uso correcto de las **3 APIs principales** del proyecto EcoPrenda:
- ✅ **Geoapify** (Mapas y Geocodificación)
- ✅ **Cloudinary** (Gestión de Imágenes)
- ✅ **Clarifai** (Detección de Prendas)

---

## 1️⃣ API GEOAPIFY (Mapas y Geocodificación)

### Configuración
| Parámetro | Ubicación | Estado |
|-----------|-----------|--------|
| `GEOAPIFY_API_KEY` | `settings.py:213` | ✅ Configurado |
| Clave por defecto | `2346b3fc49854fc9bd0017b7fa0647ca` | ℹ️ Expuesta en código |

### Uso Verificado
| Ubicación | Función | Estado |
|-----------|---------|--------|
| `views/fundacion.py:264` | Pasar clave a template para mapas | ✅ Correcto |
| `views/fundacion.py:291-297` | Geocodificación: dirección → coordenadas | ✅ Correcto |
| `views/fundacion.py:340-346` | Geocodificación de fundaciones | ✅ Correcto |

### Detalles de Implementación
```python
# Endpoint: https://api.geoapify.com/v1/geocode/search
# Parámetros:
# - text: dirección a geocodificar
# - apiKey: clave de API
# - limit: 1 (una sola respuesta)

# Extrae: coordinates[0] = lng, coordinates[1] = lat
# Se guarda en: Usuario.lng y Usuario.lat
```

### Problemas Identificados ⚠️
**CRÍTICO:** La clave API está hardcodeada en `settings.py:213`
- El valor por defecto es visible en el repositorio
- Debe usarse variable de entorno `GEOAPIFY_API_KEY`
- **Riesgo:** Acceso no autorizado, desgaste de créditos

### Recomendaciones
1. ✅ Mover la clave a `.env` (variable de entorno)
2. ✅ Regenerar la clave en Geoapify si fue comprometida
3. ✅ Agregar validación de respuesta en caso de error
4. ✅ Implementar manejo de límite de requests

---

## 2️⃣ API CLOUDINARY (Gestión de Imágenes)

### Configuración
| Parámetro | Ubicación | Estado |
|-----------|-----------|--------|
| `CLOUD_NAME` | `settings.py:217` | ✅ Configurado |
| `API_KEY` | `settings.py:218` | ✅ Configurado |
| `API_SECRET` | `settings.py:219` | ✅ Configurado |
| `DEFAULT_FILE_STORAGE` | `settings.py:223` | ✅ Configurado |

### Configuración Hardcodeada ⚠️
```python
# settings.py líneas 216-219
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': 'daev2fgjt',
    'API_KEY': '176413229185279',
    'API_SECRET': 'oCui-XzSjheafkQKxb4s_QmQ0W8'
}
```

### Archivos Auxiliares
| Archivo | Líneas | Funciones Principales |
|---------|--------|----------------------|
| `cloudinary_utils.py` | 319 líneas | 7 funciones |
| `requirements.txt` | `cloudinary==1.41.0` | ✅ Versión fija |

### Funciones Disponibles en `cloudinary_utils.py`
1. **`subir_imagen_cloudinary()`** - Sube imagen genérica
   - Carpeta: `ecoprenda` (configurable)
   - Compresión: `auto:good`
   - Formato: `auto` (WebP si soporta)

2. **`eliminar_imagen_cloudinary()`** - Elimina imagen
   - Parámetro: `public_id`

3. **`obtener_url_transformada()`** - Genera URL con transformaciones
   - Permite redimensionamiento, crop, etc.

4. **`subir_imagen_prenda()`** - Especializada para prendas
   - Tamaño: 800x800px
   - Crop: `limit` (no recorta)

5. **`subir_imagen_usuario()`** - Foto de perfil
   - Tamaño: 400x400px
   - Crop: `fill` + `gravity: face`

6. **`subir_logo_fundacion()`** - Logos
   - Tamaño: 500x500px
   - Calidad: `auto:best`
   - Fondo transparente

7. **`subir_imagen_campana()`** - Campañas
   - Tamaño: 1200x630px (Open Graph)

### Problemas Identificados ⚠️
**CRÍTICO:** Credenciales hardcodeadas en `settings.py`
- API Key y Secret visibles en repositorio
- **Riesgos:**
  - Acceso no autorizado a cuenta Cloudinary
  - Modificación/eliminación de imágenes
  - Desgaste de cuota de almacenamiento

### Dependencias Conflictivas ⚠️
En `requirements.txt` hay duplicados:
```txt
cloudinary==1.44.1     (línea 10)
cloudinary==1.41.0     (línea 15)  ← Conflicto
```
**Riesgo:** Versión incorrecta instalada

### Recomendaciones
1. ✅ Mover credenciales a variables de entorno
2. ✅ Eliminar versiones duplicadas en requirements.txt
3. ✅ Usar versión consistente de Cloudinary
4. ✅ Validar respuesta de subida antes de guardar

---

## 3️⃣ API CLARIFAI (Detección de Prendas)

### Configuración
| Parámetro | Ubicación | Estado |
|-----------|-----------|--------|
| `CLARIFAI_PAT` | `settings.py:238` | ✅ Configurado |
| `CLARIFAI_USER_ID` | `settings.py:239` | ✅ Configurado (`clarifai`) |
| `CLARIFAI_APP_ID` | `settings.py:240` | ✅ Configurado (`main`) |
| `CLARIFAI_MODEL_ID` | `settings.py:241` | ✅ Configurado (`apparel-detection`) |
| `CLARIFAI_MODEL_VERSION_ID` | `settings.py:242` | ✅ Configurado |

### Configuración Hardcodeada ⚠️
```python
# settings.py línea 238
CLARIFAI_PAT = '05b8547c887c494ba23a1c4a611c5036'
```

### Archivos Auxiliares
| Archivo | Líneas | Funciones Principales |
|---------|--------|----------------------|
| `clarifai_utils.py` | 349 líneas | 6 funciones |
| `requirements.txt` | `clarifai-grpc==10.0.9` | ✅ Versión fija |

### Funciones Disponibles en `clarifai_utils.py`
1. **`detectar_prendas_imagen()`** - Detección principal
   - Entrada: URL o bytes de imagen
   - Salida: Lista con nombre, confianza, bbox
   - Usa modelo: `apparel-detection`

2. **`mapear_categoria_clarifai()`** - Mapeo a categorías EcoPrenda
   - Convierte nombres Clarifai → categorías locales
   - Mapeo: 40+ términos → 6 categorías
   - Default: `Accesorios`

3. **`sugerir_categoria_automatica()`** - Sugerencia automática
   - Retorna categoría + confianza
   - Umbral configurable (default: 0.7)

4. **`obtener_descripcion_automatica()`** - Descripción
   - Top 3 prendas detectadas con %
   - Formato: "Detectado: shirt (98%), jeans (95%)"

5. **`validar_imagen_es_prenda()`** - Validación
   - Verifica que image contenga prenda
   - Umbral: 0.5 (configurable)

6. **`analizar_imagen_completa()`** - Análisis integral
   - Combinación de todas las anteriores
   - Retorna: validez, categoría, confianza, descripción

### Mapeo de Categorías Implementado
```python
Clarifai → EcoPrenda
─────────────────────
shirt, t-shirt, blouse, top, polo → Camiseta
pants, jeans, trousers, shorts → Pantalón
dress, gown, skirt → Vestido
jacket, coat, blazer, sweater, hoodie → Chaqueta
shoes, sneakers, boots, sandals, heels → Zapatos
bag, hat, scarf, belt, gloves, sunglasses → Accesorios
```

### Problemas Identificados ⚠️
**CRÍTICO:** PAT (Personal Access Token) hardcodeado
- Token visible en `settings.py:238`
- **Riesgos:**
  - Acceso no autorizado a Clarifai
  - Agotamiento de requests gratuitos
  - Cambio/eliminación de configuración

**IMPORTANTE:** Verificar disponibilidad de `clarifai-grpc`
- Versión 10.0.9 puede tener conflictos
- Requiere Python >= 3.7

### Recomendaciones
1. ✅ Mover PAT a variables de entorno
2. ✅ Implementar retry logic para fallos de red
3. ✅ Cachear resultados si la misma imagen se procesa múltiples veces
4. ✅ Agregar logging detallado de errores
5. ✅ Considerar procesar imágenes de manera asíncrona

---

## 🔐 PROBLEMAS DE SEGURIDAD CRÍTICOS

### 1. Credenciales Expuestas
Todas las tres APIs tienen credenciales hardcodeadas:

| API | Archivo | Línea | Tipo de Credencial |
|-----|---------|-------|-------------------|
| Geoapify | settings.py | 213 | API Key |
| Cloudinary | settings.py | 217-219 | Cloud Name, API Key, Secret |
| Clarifai | settings.py | 238 | PAT Token |

**Riesgo:** Si el repositorio es público, cualquiera puede acceder a estos recursos.

### 2. Variables de Entorno Correctas en settings.py
✅ Las variables de entorno están bien definidas:
```python
GEOAPIFY_API_KEY = os.environ.get('GEOAPIFY_API_KEY', '2346b3fc49854fc9bd0017b7fa0647ca')
CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME', 'daev2fgjt')
CLARIFAI_PAT = os.environ.get('CLARIFAI_PAT', '05b8547c887c494ba23a1c4a611c5036')
```

**Problema:** Los valores por defecto son públicos (inseguro para producción)

### 3. Archivo .env No Encontrado
No hay evidencia de archivo `.env` en el proyecto (debe estar en .gitignore)

---

## ✅ CHECKLIST DE CORRECTIVOS

- [ ] **Geoapify**
  - [ ] Regenerar API Key
  - [ ] Mover a `.env`
  - [ ] Agregar validación de respuesta
  - [ ] Implementar manejo de errores

- [ ] **Cloudinary**
  - [ ] Regenerar credentials
  - [ ] Mover a `.env`
  - [ ] Eliminar duplicados en requirements.txt
  - [ ] Usar versión consistente (1.44.1 es más reciente)
  - [ ] Validar upload response

- [ ] **Clarifai**
  - [ ] Regenerar PAT Token
  - [ ] Mover a `.env`
  - [ ] Implementar retry logic
  - [ ] Considerar caching de resultados
  - [ ] Agregar logging

- [ ] **General**
  - [ ] Crear archivo `.env.example` con estructura
  - [ ] Documentar variables de entorno necesarias
  - [ ] Agregar validación en startup

---

## 📝 CONCLUSIÓN

### Estado General: ⚠️ NECESITA CORRECCIONES CRÍTICAS

**Aspectos Positivos:**
- ✅ Todas las APIs están correctamente integradas
- ✅ Funcionalidad implementada adecuadamente
- ✅ Código bien documentado con ejemplos
- ✅ Manejo de errores básico implementado
- ✅ Transformaciones y opciones bien configuradas

**Aspectos Críticos:**
- ⚠️ Credenciales hardcodeadas en código fuente
- ⚠️ Duplicados en requirements.txt
- ⚠️ Falta validación robusta en algunas llamadas
- ⚠️ Sin logging estructurado
- ⚠️ Sin manejo de límites de rate

**Prioridad:** ALTA - Implementar cambios de seguridad antes de deploy a producción

