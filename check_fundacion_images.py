import os
import sys
import django

# Add the project directory to the Python path
sys.path.append('Proyecto')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Proyecto.settings')

# Setup Django
django.setup()

from Proyecto.App.models import Fundacion

# Check fundaciones with imagenes_adicionales
fundaciones = Fundacion.objects.filter(imagenes_adicionales__isnull=False)

print(f"Found {fundaciones.count()} fundaciones with imagenes_adicionales")

for fundacion in fundaciones:
    print(f"\nFundacion: {fundacion.nombre} (ID: {fundacion.id_fundacion})")
    print(f"Imagenes adicionales: {fundacion.imagenes_adicionales}")

    if fundacion.imagenes_adicionales:
        for i, img in enumerate(fundacion.imagenes_adicionales):
            print(f"  Image {i+1}: {img}")
            if '/media/' in img:
                print("    ⚠️  WARNING: Contains /media/ path (should be Cloudinary URL)")
            elif 'cloudinary' in img.lower():
                print("    ✅ OK: Cloudinary URL")
            else:
                print("    ❓ Unknown format")
