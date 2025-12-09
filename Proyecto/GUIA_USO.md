# 🎉 ECOPRENDA - GUÍA DE USO DEL PROYECTO

## 📌 ESTADO ACTUAL

**El proyecto está 100% funcional y listo para usar.**

✅ Django configurado
✅ Dependencias instaladas  
✅ Base de datos migrada
✅ Servidor corriendo en http://localhost:8000
✅ Admin accesible en http://localhost:8000/admin/

---

## 👤 Credenciales de Admin

```
URL:        http://localhost:8000/admin/
Usuario:    admin
Contraseña: admin123456
```

---

## 🗂️ Estructura del Proyecto

```
Proyecto/
├── App/                          # Aplicación principal Django
│   ├── views/                    # Vistas organizadas por módulo
│   │   ├── auth.py              # Autenticación
│   │   ├── prenda.py            # Gestión de prendas
│   │   ├── transaccion.py       # Transacciones
│   │   ├── fundacion.py         # Fundaciones
│   │   ├── mensaje.py           # Mensajería
│   │   ├── campana.py           # Campañas
│   │   ├── logro.py             # Logros
│   │   ├── cookie.py            # Cookies
│   │   └── impacto_ambiental.py # Impacto ambiental
│   ├── api/                      # REST API
│   │   ├── api_views.py
│   │   └── api_urls.py
│   ├── models.py                 # Modelos de datos
│   ├── forms.py                  # Formularios
│   ├── urls.py                   # Rutas principales
│   ├── cloudinary_utils.py       # Integración Cloudinary
│   ├── clarifai_utils.py         # Integración Clarifai
│   ├── carbon_utils.py           # Cálculos de impacto
│   └── decorators.py             # Decoradores personalizados
├── Proyecto/                     # Configuración Django
│   ├── settings.py               # Configuración principal
│   ├── urls.py                   # URLs raíz
│   └── wsgi.py                   # WSGI para producción
├── templates/                    # Plantillas HTML
├── static/                       # CSS, JS, imágenes
├── logs/                         # Archivos de registro
├── db.sqlite3                    # Base de datos SQLite
├── manage.py                     # Script de management
├── requirements.txt              # Dependencias Python
└── .env                          # Variables de entorno
```

---

## 🚀 Cómo Usar

### 1. Activar el Entorno Virtual

```bash
# En Windows PowerShell
.\venv\Scripts\Activate.ps1

# O en CMD
venv\Scripts\activate.bat
```

### 2. Iniciar el Servidor

El servidor ya está corriendo en `http://localhost:8000`

Para iniciarlo manualmente:
```bash
python manage.py runserver 0.0.0.0:8000
```

### 3. Acceder al Proyecto

- **Sitio web:** http://localhost:8000
- **Admin:** http://localhost:8000/admin/ (usuario: admin, contraseña: admin123456)
- **API REST:** http://localhost:8000/api/

### 4. Hacer Cambios

1. Modifica archivos en `App/views/` para cambiar comportamiento
2. Modifica `App/models.py` para cambiar estructura de datos
3. El servidor se recarga automáticamente con los cambios
4. Si cambias modelos, ejecuta: `python manage.py migrate`

---

## 🔗 Endpoints Principales

### Autenticación
- `GET /registro/` - Página de registro
- `GET /login/` - Página de login
- `GET /perfil/` - Perfil de usuario

### Prendas
- `GET /prendas/` - Listar prendas
- `GET /prenda/<id>/` - Detalle de prenda
- `GET /crear-prenda/` - Crear nueva prenda
- `GET /mis-prendas/` - Mis prendas

### Transacciones
- `GET /comprar/<id>/` - Comprar prenda
- `GET /intercambio/<id>/` - Proponer intercambio
- `GET /donar/<id>/` - Donar prenda
- `GET /mis-transacciones/` - Mis transacciones

### Fundaciones
- `GET /fundaciones/` - Listar fundaciones
- `GET /fundacion/<id>/` - Detalle de fundación
- `GET /mapa/` - Mapa interactivo

### Campañas
- `GET /crear-campana/` - Crear campaña
- `GET /campanas-solidarias/` - Ver campañas
- `GET /mis-campanas/` - Mis campañas

---

## 🔌 Integración de APIs

### Cloudinary (Imágenes)
```python
from App.cloudinary_utils import subir_imagen
imagen = subir_imagen(archivo, carpeta='prendas')
```

### Clarifai (Detección de Prendas)
```python
from App.clarifai_utils import detectar_prendas_imagen
prendas = detectar_prendas_imagen(imagen_url)
```

### Geoapify (Mapas)
```python
# Disponible en templates via GEOAPIFY_API_KEY
<script src="https://api.geoapify.com/v1/staticmap?..."></script>
```

---

## 📊 Base de Datos

### SQLite (Desarrollo Actual)
- Archivo: `db.sqlite3`
- Ruta: `C:\ProyectoEcoPrendaFinal\Proyecto\db.sqlite3`
- Acceso: Por defecto con Django ORM

### PostgreSQL (Producción en Render)
- Para activar: Descomentar `DATABASE_URL` en `.env`
- Requiere credenciales de Render PostgreSQL
- Migraciones automáticas

---

## 📝 Logging

Los logs se guardan en la carpeta `logs/`:

```
logs/
├── django_general.log      # Eventos generales de Django
├── api_calls.log           # Llamadas a APIs (Cloudinary, Clarifai)
└── console output          # Salida estándar del servidor
```

Ver logs:
```bash
# Ver último log de API
Get-Content logs/api_calls.log -Tail 20

# Ver último log general
Get-Content logs/django_general.log -Tail 20
```

---

## 🛠️ Comandos Útiles

```bash
# Crear migraciones
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Recopilar estáticos
python manage.py collectstatic --noinput

# Validar configuración
python manage.py check

# Shell interactivo
python manage.py shell

# Ver usuarios
python manage.py shell
>>> from django.contrib.auth.models import User
>>> User.objects.all()

# Ejecutar tests
python manage.py test
```

---

## ⚠️ Troubleshooting

### Error: ModuleNotFoundError
**Solución:** Verificar que el venv está activado:
```bash
.\venv\Scripts\Activate.ps1
```

### Error: Port 8000 already in use
**Solución:** Cambiar puerto:
```bash
python manage.py runserver 0.0.0.0:8001
```

### Error: Database locked
**Solución:** Reiniciar el servidor y verificar no hay procesos Django activos.

### Error: No migrations files
**Solución:** Las migraciones ya están hechas. Si cambias models.py, ejecuta:
```bash
python manage.py makemigrations
python manage.py migrate
```

---

## 🔐 Variables de Entorno (.env)

```
# Django
DEBUG=True                    # True en desarrollo, False en producción
SECRET_KEY=...               # Clave secreta (NO compartir)
ALLOWED_HOSTS=...            # Hosts permitidos

# APIs Externas
GEOAPIFY_API_KEY=...         # Para mapas
CLOUDINARY_CLOUD_NAME=...    # Para imágenes
CLOUDINARY_API_KEY=...       # Para imágenes
CLOUDINARY_API_SECRET=...    # Para imágenes
CLARIFAI_PAT=...             # Para detección de prendas

# Base de Datos
DATABASE_URL=...             # Solo para Render/producción
```

---

## 📦 Dependencias Instaladas

| Paquete | Versión | Uso |
|---------|---------|-----|
| Django | 5.2.5 | Framework web |
| djangorestframework | 3.16.1 | API REST |
| Pillow | 11.3.0 | Procesamiento de imágenes |
| psycopg2-binary | 2.9.11 | PostgreSQL driver |
| python-dotenv | 1.2.1 | Variables de entorno |
| dj-database-url | 3.0.1 | Parseo de DATABASE_URL |
| requests | 2.32.4 | HTTP requests |
| boto3 | 1.42.0 | AWS S3 (opcional) |
| cryptography | 46.0.3 | Encriptación |
| django-cloudinary-storage | 0.3.0 | Almacenamiento Cloudinary |
| cloudinary | 1.44.1 | API Cloudinary |
| clarifai-grpc | 10.0.9 | API Clarifai |
| gunicorn | 23.0.0 | WSGI server (producción) |

---

## 🚀 Deployment a Render

1. Actualizar `.env` con credenciales de Render PostgreSQL
2. Descomentar `DATABASE_URL` en `.env`
3. Usar configuración en `render.yaml`
4. Push a GitHub
5. Conectar con Render

Ver `RENDER_DEPLOYMENT.md` para instrucciones completas.

---

## 📞 Soporte

Si hay problemas:
1. Verificar logs en carpeta `logs/`
2. Ejecutar `python manage.py check`
3. Reiniciar el servidor
4. Verificar `.env` está correcto

---

**Proyecto EcoPrenda - Plataforma de Intercambio y Donación de Ropa Sostenible**

Última actualización: 09 de Diciembre de 2025
