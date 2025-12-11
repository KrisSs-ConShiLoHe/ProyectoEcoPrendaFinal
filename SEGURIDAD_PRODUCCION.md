# 🔒 RECOMENDACIONES DE SEGURIDAD PARA PRODUCCIÓN EN RENDER

## Estado Actual
Tu configuración está **bien estructurada** pero necesita ajustes de seguridad para producción.

---

## 🚨 CAMBIOS CRÍTICOS NECESARIOS

### 1. **HTTPS/SSL (OBLIGATORIO)**

En `settings.py`, descomenta y activa (o crea `settings_prod.py`):

```python
# En producción SIEMPRE activar HTTPS
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# HSTS (HTTP Strict-Transport-Security)
SECURE_HSTS_SECONDS = 31536000  # 1 año
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

**Por qué**: Encrypt todas las comunicaciones cliente-servidor. Render proporciona SSL automático.

---

### 2. **DEBUG = False (CRÍTICO)**

Asegurar en Render:
```
DEBUG = False
```

**Por qué**: En `DEBUG=True`, Django expone rutas, variables de entorno, stacktraces completos.

---

### 3. **SECRET_KEY Fuerte**

Render genera uno automático con `generateValue: true` en `render.yaml`. ✅

**Verificar**: En Render Dashboard → Environment, debe existir `SECRET_KEY` y tener ~50 caracteres.

---

### 4. **Credenciales de API**

**Uso seguro**:
- ✅ Guardar en Render Environment (variables de entorno)
- ✅ NUNCA commitear `.env` a Git
- ✅ Rotar credenciales regularmente

**Verificar**:
```bash
# Verificar que NO están en el código
grep -r "CLOUDINARY_API_KEY\s*=" Proyecto/App/views/
grep -r "CLARIFAI_PAT\s*=" Proyecto/App/views/
```

Debería estar SOLO en `settings.py` leyendo variables:
```python
CLOUDINARY_API_KEY = os.environ.get('CLOUDINARY_API_KEY')
```

---

### 5. **Configurar Email para Alertas**

En `settings.py` agregar:
```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # Desarrollo
# O para producción:
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
```

**Para qué**: Enviar alertas de error, resets de contraseña, etc.

---

## 📋 CAMBIOS RECOMENDADOS (NO CRÍTICOS)

### 1. **Crear settings_prod.py Separado**

Mejor práctica: mantener settings_local.py y settings_prod.py separados.

```python
# Proyecto/settings_prod.py
from .settings import *

DEBUG = False
ALLOWED_HOSTS = ['proyectoecoprenda-ykp.onrender.com', 'www.proyectoecoprenda-ykp.onrender.com']

# Seguridad adicional
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Compresión
COMPRESS_ENABLED = True
COMPRESS_OFFLINE = True
```

Luego en `render.yaml`:
```yaml
buildCommand: ... python manage.py migrate --settings=Proyecto.settings_prod
startCommand: ... gunicorn Proyecto.wsgi:application --settings=Proyecto.settings_prod
```

---

### 2. **Agregar Compresión GZip**

En `requirements.txt`:
```
django-compressor==4.1
```

En `settings.py`:
```python
INSTALLED_APPS += ['compressor']
COMPRESS_ENABLED = True
COMPRESS_OFFLINE = True
```

**Beneficio**: Reducir ancho de banda ~70%

---

### 3. **Caché en Render**

En `settings.py`:
```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'ecoprenda-cache',
    }
}
```

O si usas Redis en Render:
```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1'),
    }
}
```

---

### 4. **Logging Mejorado para Producción**

```python
# En settings_prod.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/django_errors.log',
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 5,
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'ERROR',
    },
}
```

---

## ✅ CHECKLIST DE SEGURIDAD

- [ ] `DEBUG = False` en producción
- [ ] `SECRET_KEY` generado y único en Render
- [ ] HTTPS/SSL activado (Render lo hace automático)
- [ ] HSTS headers configurados
- [ ] Todas las credenciales en variables de entorno
- [ ] `.env` en `.gitignore` (ya lo está)
- [ ] CSRF Protection activo
- [ ] Session cookies con `SECURE=True` y `HTTPONLY=True`
- [ ] X-Frame-Options = DENY (ya está)
- [ ] Email configurado para alertas
- [ ] Backups de PostgreSQL configurados en Render
- [ ] Logs monitoreados regularmente

---

## 🚀 DEPLOYMENT FINAL

Cuando todo esté listo:

1. Actualizar `render.yaml` con settings_prod
2. Actualizar variables de entorno en Render
3. Push a main branch
4. Render redeploy automático
5. Verificar HTTPS funciona
6. Probar flujos completos (registro, login, crear prenda)

