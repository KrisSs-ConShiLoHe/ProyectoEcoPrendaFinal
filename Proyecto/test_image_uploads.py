import os
import django
from django.test import TestCase, Client
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.urls import reverse
from App.models import Usuario, Prenda, Fundacion

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Proyecto.settings')
django.setup()

class ImageUploadTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create a test user
        self.user = Usuario.objects.create_user(
            correo='test@example.com',
            contrasena='password123',
            nombre='Test User',
            rol='CLIENTE'
        )
        # Create a test prenda
        self.prenda = Prenda.objects.create(
            titulo='Test Prenda',
            descripcion='Test description',
            user=self.user,
            estado='DISPONIBLE'
        )
        # Create a test fundacion
        self.fundacion = Fundacion.objects.create(
            nombre='Test Fundacion',
            descripcion='Test description',
            representante=self.user
        )

    def test_actualizar_foto_perfil_valid_image(self):
        # Login the user
        self.client.post(reverse('login'), {
            'correo': 'test@example.com',
            'contrasena': 'password123'
        })
        # Create a valid image file
        image = SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
        response = self.client.post(reverse('actualizar_foto_perfil'), {
            'imagen_usuario': image
        })
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.user.refresh_from_db()
        self.assertTrue(self.user.imagen_usuario.startswith('http'))  # Should be Cloudinary URL

    def test_actualizar_foto_perfil_invalid_image(self):
        # Login the user
        self.client.post(reverse('login'), {
            'correo': 'test@example.com',
            'contrasena': 'password123'
        })
        # Create an invalid image file (too large)
        large_content = b"x" * (6 * 1024 * 1024)  # 6MB
        image = SimpleUploadedFile("test.jpg", large_content, content_type="image/jpeg")
        response = self.client.post(reverse('actualizar_foto_perfil'), {
            'imagen_usuario': image
        })
        self.assertEqual(response.status_code, 302)  # Redirect with error

    def test_actualizar_imagen_prenda_valid_image(self):
        # Login the user
        self.client.post(reverse('login'), {
            'correo': 'test@example.com',
            'contrasena': 'password123'
        })
        # Create a valid image file
        image = SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
        response = self.client.post(reverse('actualizar_imagen_prenda', args=[self.prenda.id_prenda]), {
            'imagen_prenda': image
        })
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.prenda.refresh_from_db()
        self.assertTrue(self.prenda.imagen_prenda.startswith('http'))  # Should be Cloudinary URL

    def test_actualizar_logo_fundacion_valid_image(self):
        # Login the user
        self.client.post(reverse('login'), {
            'correo': 'test@example.com',
            'contrasena': 'password123'
        })
        # Create a valid image file
        image = SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
        response = self.client.post(reverse('actualizar_logo_fundacion', args=[self.fundacion.id_fundacion]), {
            'imagen_fundacion': image
        })
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.fundacion.refresh_from_db()
        self.assertTrue(self.fundacion.imagen_fundacion.startswith('http'))  # Should be Cloudinary URL

if __name__ == '__main__':
    import unittest
    unittest.main()
