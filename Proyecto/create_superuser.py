import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Proyecto.settings')
django.setup()

from django.contrib.auth.models import User

# Crear superusuario si no existe
username = 'admin'
email = 'admin@ecoprenda.com'
password = 'admin123456'

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print(f"✅ Superusuario '{username}' creado exitosamente")
    print(f"   Email: {email}")
    print(f"   Contraseña: {password}")
else:
    print(f"⚠️  El superusuario '{username}' ya existe")

# Mostrar información
print("\n📋 Información del proyecto:")
print("   URL de administración: http://localhost:8000/admin/")
print("   Usuario: admin")
print("   Contraseña: admin123456")
