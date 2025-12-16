import os
import sys
import django

# Add the project directory to the Python path
sys.path.append('Proyecto')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Proyecto.settings')

# Setup Django
django.setup()

from Proyecto.App.models import Fundacion

def fix_fundacion_images():
    """Clean up invalid /media/ paths in fundacion imagenes_adicionales"""

    print("🔍 Checking fundaciones with imagenes_adicionales...")

    # Get all fundaciones with imagenes_adicionales
    fundaciones = Fundacion.objects.filter(imagenes_adicionales__isnull=False)

    fixed_count = 0
    total_invalid = 0

    for fundacion in fundaciones:
        original_list = fundacion.imagenes_adicionales or []
        cleaned_list = []
        has_changes = False

        print(f"\n📁 Fundacion: {fundacion.nombre} (ID: {fundacion.id_fundacion})")

        for i, img_url in enumerate(original_list):
            if isinstance(img_url, str) and '/media/' in img_url:
                print(f"  ❌ Removing invalid local path: {img_url}")
                total_invalid += 1
                has_changes = True
                # Skip this invalid URL
                continue
            else:
                # Keep valid URLs (Cloudinary or others)
                cleaned_list.append(img_url)

        if has_changes:
            print(f"  ✅ Updating imagenes_adicionales: {len(original_list)} -> {len(cleaned_list)} images")
            fundacion.imagenes_adicionales = cleaned_list
            fundacion.save()
            fixed_count += 1
        else:
            print("  ✅ No invalid paths found")

    print("
📊 Summary:"    print(f"  - Fundaciones checked: {fundaciones.count()}")
    print(f"  - Fundaciones fixed: {fixed_count}")
    print(f"  - Invalid paths removed: {total_invalid}")

    if total_invalid > 0:
        print("
✅ Database cleanup completed!"    else:
        print("
✅ No invalid paths found - database is clean!"if __name__ == '__main__':
    fix_fundacion_images()
