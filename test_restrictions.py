import os
import sys
import django
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Proyecto.Proyecto.settings')
django.setup()

from Proyecto.App.models import Usuario, Fundacion

def test_representative_restrictions():
    """Test that representatives are restricted from accessing personal views"""

    # Create test client
    client = Client()

    # Create a foundation
    fundacion = Fundacion.objects.create(
        nombre="Fundación Test",
        descripcion="Fundación para pruebas",
        activa=True
    )

    # Create a representative user
    User = get_user_model()
    representante = User.objects.create_user(
        username='representante_test',
        email='rep@test.com',
        password='test123',
        rol='REPRESENTANTE_FUNDACION'
    )
    representante.fundacion_asignada = fundacion
    representante.save()

    # Create a client user for comparison
    cliente = User.objects.create_user(
        username='cliente_test',
        email='cliente@test.com',
        password='test123',
        rol='CLIENTE'
    )

    print("Testing representative restrictions...")

    # Test URLs that should be restricted for representatives
    restricted_urls = [
        ('mis_prendas', 'mis prendas'),
        ('mis_transacciones', 'mis transacciones'),
        ('mi_impacto', 'mi impacto'),
        ('mis_logros', 'mis logros'),
    ]

    # Login as representative
    client.login(username='representante_test', password='test123')

    for url_name, view_name in restricted_urls:
        try:
            url = reverse(url_name)
            response = client.get(url, follow=True)
            if response.status_code == 200:
                # Check if redirected to home
                if 'home' in response.request['PATH_INFO'] or response.request['PATH_INFO'] == '/':
                    print(f"✓ {view_name}: Representative correctly redirected to home")
                else:
                    print(f"✗ {view_name}: Representative not redirected properly")
            else:
                print(f"✗ {view_name}: Unexpected status code {response.status_code}")
        except Exception as e:
            print(f"✗ {view_name}: Error testing - {e}")

    # Test that client can access these views
    client.logout()
    client.login(username='cliente_test', password='test123')

    print("\nTesting client access...")
    for url_name, view_name in restricted_urls:
        try:
            url = reverse(url_name)
            response = client.get(url)
            if response.status_code == 200:
                print(f"✓ {view_name}: Client can access normally")
            else:
                print(f"✗ {view_name}: Client cannot access - status {response.status_code}")
        except Exception as e:
            print(f"✗ {view_name}: Error testing client access - {e}")

    # Cleanup
    representante.delete()
    cliente.delete()
    fundacion.delete()

    print("\nTest completed!")

if __name__ == '__main__':
    test_representative_restrictions()
