# 🚀 Guía de Deployment en Render - EcoPrenda

## ✅ Checklist Pre-Deployment

Antes de deployar en Render, asegúrate de:

- [ ] Credenciales correctas en `.env` (local)
- [ ] `python Proyecto/manage.py check` sin errores
- [ ] `python Proyecto/manage.py migrate` ejecutado localmente
- [ ] Cambios commiteados a Git (rama `main`)
- [ ] `.env` NO está en Git (debe estar en `.gitignore`)

---

## 📋 Pasos para Deployar en Render

### 1. Crear cuenta en Render
- Ir a https://render.com/
- Registrarse con GitHub
- Autorizar acceso al repositorio

### 2. Crear Web Service
1. Dashboard → **New +** → **Web Service**
2. Seleccionar repo `ProyectoEcoPrendaFinal`
3. Conectar rama `main`
4. Llenar campos:
   - **Name:** `ecoprenda-app` (o similar)
   - **Runtime:** `Python 3.11`
   - **Build Command:**
     ```bash
     pip install -r Proyecto/requirements.txt && cd Proyecto && python manage.py migrate && python manage.py collectstatic --noinput
     ```
   - **Start Command:**
     ```bash
     cd Proyecto && gunicorn Proyecto.wsgi:application --bind 0.0.0.0:$PORT
     ```
   - **Plan:** Free (o pago según necesites)

### 3. Configurar Variables de Entorno
En Render Dashboard → Settings → Environment:

Agregar TODAS estas variables:

```env
DEBUG=False
SECRET_KEY=<generar-una-clave-fuerte>
ALLOWED_HOSTS=ecoprenda-app.onrender.com

DATABASE_URL=<tu-postgresql-url-desde-render>

GEOAPIFY_API_KEY=<tu-clave>
CLOUDINARY_CLOUD_NAME=<tu-cloud-name>
CLOUDINARY_API_KEY=<tu-api-key>
CLOUDINARY_API_SECRET=<tu-api-secret>
CLARIFAI_PAT=<tu-pat-token>
```

### 4. Crear PostgreSQL en Render
1. Dashboard → **New +** → **PostgreSQL**
2. Llenar:
   - **Name:** `ecoprenda-db`
   - **Plan:** Free
   - **Region:** Misma que el Web Service
3. Copiar `DATABASE_URL` generado en Render → agregar a Environment del Web Service

### 5. Deployar
Render automáticamente:
- ✅ Clona el repo
- ✅ Instala dependencias
- ✅ Ejecuta migraciones
- ✅ Recolecta static files
- ✅ Inicia el servidor con Gunicorn

---

## 🔍 Monitorear Deployment

1. Ir a **Logs** en Render Dashboard
2. Ver progreso en tiempo real
3. Esperar a ver: `Server running at ...`

---

## 🧪 Pruebas Post-Deployment

```bash
# 1. Verificar sitio está en línea
curl https://ecoprenda-app.onrender.com/

# 2. Verificar APIs funcionan
curl https://ecoprenda-app.onrender.com/admin/

# 3. Verificar BD está conectada
# Intentar login o crear usuario desde interfaz web
```

---

## 🐛 Solución de Problemas

### Error: `ModuleNotFoundError: No module named 'dj_database_url'`
✅ **Solución:** Verificar que `requirements.txt` contiene `dj-database-url==3.0.1`

### Error: `ImproperlyConfigured: DEBUG must be False if ALLOWED_HOSTS is empty`
✅ **Solución:** Configurar `DEBUG=False` y `ALLOWED_HOSTS=ecoprenda-app.onrender.com` en Render

### Error: `OperationalError: could not connect to server: Connection refused`
✅ **Solución:** Verificar que `DATABASE_URL` está configurado correctamente en Render

### Sitio devuelve 500 (Internal Server Error)
✅ **Solución:** 
1. Ver logs en Render Dashboard
2. Ejecutar localmente: `python Proyecto/manage.py check`
3. Verificar variables de entorno en Render

### Static files no cargan (404 en `/static/`)
✅ **Solución:**
1. Ejecutar `collectstatic` manual en Render console
2. Verificar `STATIC_ROOT` en `settings.py`
3. Reiniciar el Web Service

---

## 🔄 Hacer Cambios Después del Deployment

1. Editar código localmente
2. Hacer commit y push a `main`
3. Render automáticamente:
   - Detecta cambios
   - Recompila
   - Ejecuta migraciones si las hay
   - Redeploya

---

## 📊 Monitoreo y Mantenimiento

### Ver logs en tiempo real
```bash
# Desde Render Dashboard → Logs
# O usar CLI si instalaste render-cli
render logs --service <service-id>
```

### Forzar redeploy sin cambios
Render Dashboard → Deploys → **Redeploy** en el último deployment

### Ver uso de recursos
Dashboard → **Metrics** → CPU, Memoria, Disco

---

## 💾 Backup de Base de Datos

Render mantiene backups automáticos (plan Pro).
Para descargar:
1. Ir a PostgreSQL → Backups
2. Seleccionar backup
3. Descargar

---

## 🚨 Notas de Seguridad

- ✅ Nunca commitees `.env` con credenciales
- ✅ Regenera `SECRET_KEY` en Render (diferente a desarrollo)
- ✅ Usa HTTPS siempre (Render lo proporciona)
- ✅ Cambia contraseñas de APIs si las compartiste
- ✅ Revisa logs regularmente para anomalías

---

## 📝 Archivo render.yaml

Si prefieres usar `render.yaml` en lugar de configurar manualmente:

```yaml
services:
  - type: web
    name: ecoprenda-app
    runtime: python
    buildCommand: pip install -r Proyecto/requirements.txt && cd Proyecto && python manage.py migrate && python manage.py collectstatic --noinput
    startCommand: cd Proyecto && gunicorn Proyecto.wsgi:application --bind 0.0.0.0:$PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.11
      - key: DEBUG
        value: "False"
```

Luego solo necesitas agregar secretos desde Dashboard.

---

## 🎯 URLs Importantes

- **Dashboard:** https://dashboard.render.com/
- **Docs:** https://render.com/docs/
- **Status:** https://render.com/status

