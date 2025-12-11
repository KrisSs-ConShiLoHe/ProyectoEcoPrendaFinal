# ✅ CHECKLIST DE DEPLOY EN RENDER

## Pre-Deploy (Local)
- [ ] Ejecutar `python manage.py migrate --settings=Proyecto.settings_local` localmente
- [ ] Ejecutar `python manage.py collectstatic --noinput --settings=Proyecto.settings_local`
- [ ] Probar `python manage.py runserver --settings=Proyecto.settings_local` sin errores
- [ ] Verificar que no hay cambios sin committear en Git
- [ ] Commit y push a `main` branch

---

## En Render Dashboard

### 1. **Crear PostgreSQL Database**
- [ ] Ir a Render Dashboard → "New +" → "PostgreSQL"
- [ ] Crear database (ej: `ecoprenda-db`)
- [ ] Anotar la `DATABASE_URL` completa
- [ ] Copiar la URL completa (incluye credenciales)

### 2. **Crear Web Service**
- [ ] Ir a Render Dashboard → "New +" → "Web Service"
- [ ] Conectar repo GitHub: `ProyectoEcoPrendaFinal`
- [ ] Seleccionar branch: `main`
- [ ] Llenar datos:
  - **Name**: `ecoprenda-app`
  - **Runtime**: Python 3.11
  - **Build Command**: Dejará el del `render.yaml`
  - **Start Command**: Dejará el del `render.yaml`

### 3. **Configurar Variables de Entorno**

En la sección "Environment" del Web Service, agregar TODAS estas:

#### ✅ Básicas (críticas):
```
DATABASE_URL = [Pegar la URL completa de PostgreSQL]
DEBUG = False
SECRET_KEY = [Render la genera automáticamente]
ALLOWED_HOSTS = proyectoecoprenda-ykp.onrender.com,www.proyectoecoprenda-ykp.onrender.com
```

#### 🗺️ Geoapify (Mapas):
```
GEOAPIFY_API_KEY = [Tu clave de Geoapify]
```
Obtener en: https://geoapify.com/sign-up

#### ☁️ Cloudinary (Imágenes):
```
CLOUDINARY_CLOUD_NAME = [Tu cloud name]
CLOUDINARY_API_KEY = [Tu API key]
CLOUDINARY_API_SECRET = [Tu API secret]
```
Obtener en: https://cloudinary.com/console

#### 🤖 Clarifai (Detección IA):
```
CLARIFAI_PAT = [Tu Personal Access Token]
CLARIFAI_USER_ID = [Tu user ID]
CLARIFAI_APP_ID = [Tu app ID]
CLARIFAI_MODEL_ID = [Tu model ID]
CLARIFAI_MODEL_VERSION_ID = [Tu model version ID]
```
Obtener en: https://clarifai.com

---

## Deploy
- [ ] Clickear "Deploy" en Render
- [ ] Esperar a que compile y corra migraciones (~5-10 minutos)
- [ ] Ver logs en "Logs" tab
- [ ] Verificar que el sitio esté UP en: https://proyectoecoprenda-ykp.onrender.com

---

## Post-Deploy - Pruebas
- [ ] [ ] Ir a https://proyectoecoprenda-ykp.onrender.com
- [ ] [ ] Página home carga correctamente
- [ ] [ ] Registro de usuario funciona
- [ ] [ ] Login funciona
- [ ] [ ] Crear prenda funciona (si Cloudinary está configurado)
- [ ] [ ] Mapa carga (si Geoapify está configurado)

---

## Troubleshooting

### ❌ "ModuleNotFoundError: No module named 'clarifai'"
**Solución**: Asegurar que `clarifai-grpc==10.0.9` está en `requirements.txt`

### ❌ "ImproperlyConfigured: CLOUDINARY_API_KEY not configured"
**Solución**: Agregar variables de Cloudinary a Render Environment

### ❌ Database migration fails
**Solución**: 
1. En Render, resetear la database
2. Ir a "PostgreSQL" → Settings → "Delete all data"
3. Re-deploy

### ❌ Static files not loading (404 on CSS/JS)
**Solución**: 
1. Asegurar `python manage.py collectstatic` corrió en build
2. Verificar que `STATIC_ROOT` y `STATIC_URL` son correctas en `settings.py`

---

## Monitoreo Continuo
- [ ] Revisar logs regularmente: `Render Dashboard → Logs`
- [ ] Configurar alertas de error en Render
- [ ] Hacer backup de la database PostgreSQL regularmente

