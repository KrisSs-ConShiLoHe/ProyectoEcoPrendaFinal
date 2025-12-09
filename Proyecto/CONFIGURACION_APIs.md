# 🔐 Configuración de APIs - EcoPrenda

## ⚠️ IMPORTANTE: Configuración de Credenciales

Este proyecto utiliza tres APIs externas. **NUNCA commitees las credenciales a Git**.

### Paso 1: Crear archivo `.env`

1. Copia el archivo `.env.example` a `.env`:
   ```bash
   cp .env.example .env
   ```

2. **NO COMMITEES `.env` A GIT** - Ya está en `.gitignore`

### Paso 2: Obtener Credenciales

#### 🗺️ **GEOAPIFY** (Mapas y Geocodificación)
1. Ir a https://myprojects.geoapify.com/
2. Registrarse o iniciar sesión
3. Copiar la **API Key**
4. Pegarlo en `.env`:
   ```env
   GEOAPIFY_API_KEY=tu_clave_aqui
   ```

#### 📷 **CLOUDINARY** (Gestión de Imágenes)
1. Ir a https://cloudinary.com/console
2. Registrarse o iniciar sesión
3. En el dashboard, copiar:
   - **Cloud Name**
   - **API Key**
   - **API Secret**
4. Pegarlo en `.env`:
   ```env
   CLOUDINARY_CLOUD_NAME=tu_cloud_name
   CLOUDINARY_API_KEY=tu_api_key
   CLOUDINARY_API_SECRET=tu_api_secret
   ```

#### 🤖 **CLARIFAI** (Detección de Prendas con IA)
1. Ir a https://clarifai.com/
2. Registrarse o iniciar sesión
3. Ir a Settings → Personal Access Tokens
4. Crear un nuevo **PAT Token**
5. Pegarlo en `.env`:
   ```env
   CLARIFAI_PAT=tu_token_aqui
   ```

### Paso 3: Verificar Configuración

Ejecuta el script de verificación:
```bash
python test_apis.py
```

**Resultado esperado:**
```
✅ GEOAPIFY_API_KEY configurada
✅ CLOUDINARY_CLOUD_NAME configurada
✅ CLOUDINARY_API_KEY configurada
✅ CLOUDINARY_API_SECRET configurada
✅ CLARIFAI_PAT configurada
✅ TODAS LAS APIs ESTÁN CORRECTAMENTE CONFIGURADAS
```

### Paso 4: Instalar Dependencias

```bash
pip install -r requirements.txt
```

---

## 📋 Estructura de `.env`

```env
# ==================== GEOAPIFY ====================
GEOAPIFY_API_KEY=2346b3fc49854fc9bd0017b7fa0647ca

# ==================== CLOUDINARY ====================
CLOUDINARY_CLOUD_NAME=tu_cloud_name
CLOUDINARY_API_KEY=176413229185279
CLOUDINARY_API_SECRET=oCui-XzSjheafkQKxb4s_QmQ0W8

# ==================== CLARIFAI ====================
CLARIFAI_PAT=05b8547c887c494ba23a1c4a611c5036

# ==================== DJANGO ====================
DEBUG=True
SECRET_KEY=tu-clave-secreta-aqui
ALLOWED_HOSTS=localhost,127.0.0.1

# ==================== BASE DE DATOS ====================
DATABASE_URL=postgresql://user:password@localhost:5432/ecoprenda
```

---

## 🔒 Seguridad

### ✅ Buenas Prácticas Implementadas

1. **Credenciales en variables de entorno** - No hardcodeadas en el código
2. **Archivo `.gitignore`** - Previene commits accidentales
3. **`.env.example`** - Documenta la estructura sin exponer secretos
4. **Validación en producción** - Falla si faltan credenciales en DEBUG=False
5. **Logging estructurado** - Rastrea errores sin exponer credenciales

### ❌ ¿Qué NO hacer?

- ❌ Commitear `.env` a Git
- ❌ Compartir credenciales por email o chat
- ❌ Hardcodear credenciales en archivos Python
- ❌ Usar la misma clave en producción y desarrollo
- ❌ Exponer el código fuente con credenciales

---

## 🧪 Pruebas de APIs

### Probar GEOAPIFY
```python
from django.conf import settings
import requests

response = requests.get(
    'https://api.geoapify.com/v1/geocode/search',
    params={
        'text': 'Santiago, Chile',
        'apiKey': settings.GEOAPIFY_API_KEY,
    }
)
print(response.json())
```

### Probar CLOUDINARY
```python
from App.cloudinary_utils import subir_imagen_cloudinary

# En una vista Django
resultado = subir_imagen_cloudinary(
    imagen=request.FILES['imagen'],
    carpeta='test'
)
print(resultado)
```

### Probar CLARIFAI
```python
from App.clarifai_utils import detectar_prendas_imagen

prendas = detectar_prendas_imagen(
    imagen_url='https://example.com/image.jpg'
)
print(prendas)
```

---

## 📊 Límites de APIs

### Geoapify
- **Plan Gratuito:** 3,000 requests/mes
- **Límite por request:** 1 ubicación

### Cloudinary
- **Plan Gratuito:** 25 GB almacenamiento, 25 GB transformaciones
- **Subidas diarias:** Sin límite

### Clarifai
- **Plan Gratuito:** 5,000 calls/mes
- **Modelo:** apparel-detection pre-entrenado

---

## 📝 Logging

Los logs se guardan en:
- `logs/ecoprenda.log` - Logs generales
- `logs/apis.log` - Logs específicos de APIs

### Ver logs en tiempo real
```bash
tail -f logs/apis.log
```

### Niveles de log
- `DEBUG` - Información detallada (desarrollo)
- `INFO` - Eventos normales
- `WARNING` - Advertencias
- `ERROR` - Errores
- `CRITICAL` - Errores críticos

---

## 🚨 Solución de Problemas

### Error: "GEOAPIFY_API_KEY no está configurada"
✅ Verifica que `.env` tiene la clave configurada
✅ Ejecuta `python test_apis.py`
✅ Reinicia el servidor Django

### Error: "CLOUDINARY_STORAGE no tiene CLOUD_NAME"
✅ Verifica que todas las tres credenciales están en `.env`
✅ Verifica que no hay espacios en blanco
✅ Regenera las credenciales en Cloudinary

### Error: "CLARIFAI_PAT authentication failed"
✅ Verifica que el PAT Token es válido
✅ Regenera el token en https://clarifai.com/settings/tokens
✅ Verifica que la imagen URL es accesible

---

## 📚 Referencias

- [Documentación Geoapify](https://apidocs.geoapify.com/)
- [Documentación Cloudinary](https://cloudinary.com/documentation)
- [Documentación Clarifai](https://clarifai.com/developers/documentation)

---

## ✅ Checklist de Configuración

- [ ] Crear `.env` desde `.env.example`
- [ ] Obtener credenciales de Geoapify
- [ ] Obtener credenciales de Cloudinary
- [ ] Obtener PAT Token de Clarifai
- [ ] Llenar todas las credenciales en `.env`
- [ ] Ejecutar `python test_apis.py`
- [ ] Ver resultado: "✅ TODAS LAS APIs ESTÁN CONFIGURADAS"
- [ ] Instalar dependencias: `pip install -r requirements.txt`
- [ ] Verificar que `.env` NO está en Git

