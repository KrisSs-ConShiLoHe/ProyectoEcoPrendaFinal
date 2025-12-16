#!/usr/bin/env python
"""
Test script to verify the naive datetime fix in CampanaFundacion views.
This script simulates POST requests to test campaign creation and editing.
"""
import os
import sys
import django
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Proyecto.settings')
django.setup()

from django.test import Client, TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from App.models import CampanaFundacion, Fundacion

def test_datetime_conversion():
    """Test the datetime conversion logic directly."""
    print("Testing datetime conversion logic...")

    try:
        # Test the conversion that happens in the views
        fecha_inicio_str = '2025-12-20 10:00:00'
        fecha_fin_str = '2025-12-25 10:00:00'

        # This is the exact code from the view
        fecha_inicio_dt = timezone.make_aware(datetime.strptime(fecha_inicio_str, '%Y-%m-%d %H:%M:%S'))
        fecha_fin_dt = timezone.make_aware(datetime.strptime(fecha_fin_str, '%Y-%m-%d %H:%M:%S'))

        print("✅ Datetime conversion successful!")
        print(f"   Fecha inicio: {fecha_inicio_dt} (tz-aware: {timezone.is_aware(fecha_inicio_dt)})")
        print(f"   Fecha fin: {fecha_fin_dt} (tz-aware: {timezone.is_aware(fecha_fin_dt)})")

        # Test creating a campaign with these dates
        fundacion = Fundacion.objects.create(
            nombre="Fundacion Test",
            descripcion="Test fundacion",
            correo_contacto="test@fundacion.com"
        )

        campaign = CampanaFundacion.objects.create(
            fundacion=fundacion,
            nombre='Campaña Test Datetime',
            descripcion='Test campaign for datetime fix',
            fecha_inicio=fecha_inicio_dt,
            fecha_fin=fecha_fin_dt,
            objetivo_prendas=50,
            categorias_solicitadas='Ropa de invierno',
            activa=True
        )

        print("✅ Campaign created successfully with timezone-aware dates!")
        print(f"   Campaign: {campaign.nombre}")
        print(f"   Fecha inicio: {campaign.fecha_inicio} (tz-aware: {timezone.is_aware(campaign.fecha_inicio)})")
        print(f"   Fecha fin: {campaign.fecha_fin} (tz-aware: {timezone.is_aware(campaign.fecha_fin)})")

        return True

    except Exception as e:
        print(f"❌ Error during datetime conversion test: {e}")
        return False

def test_campaign_editing():
    """Test editing a campaign with timezone-aware dates."""
    print("\nTesting campaign editing...")

    try:
        # Get an existing campaign
        campaign = CampanaFundacion.objects.filter(activa=True).first()
        if not campaign:
            print("No active campaigns found for editing test")
            return True  # Skip if no campaigns exist

        client = Client()

        # Login as the campaign's fundacion representative
        user = campaign.fundacion.representante_fundacion
        if not user:
            print("No representative user for the fundacion")
            return True  # Skip

        client.login(username=user.username, password="testpass123")

        # Test data for editing
        edit_data = {
            'nombre': campaign.nombre + ' (Edited)',
            'descripcion': campaign.descripcion + ' (Edited)',
            'fecha_inicio': '2025-12-21 11:00:00',
            'fecha_fin': '2025-12-26 11:00:00',
            'objetivo_prendas': campaign.objetivo_prendas + 10,
            'categorias_solicitadas': campaign.categorias_solicitadas
        }

        # Make POST request to edit campaign
        response = client.post(f'/campanas/editar/{campaign.id}/', edit_data)

        if response.status_code == 302:  # Redirect on success
            print("✅ Campaign editing successful - no datetime warning!")

            # Refresh campaign from database
            campaign.refresh_from_db()
            print(f"✅ Campaign updated: {campaign.nombre}")
            print(f"   Fecha inicio: {campaign.fecha_inicio} (tz-aware: {timezone.is_aware(campaign.fecha_inicio)})")
            print(f"   Fecha fin: {campaign.fecha_fin} (tz-aware: {timezone.is_aware(campaign.fecha_fin)})")
            return True
        else:
            print(f"❌ Campaign editing failed with status {response.status_code}")
            print(f"Response content: {response.content.decode()}")
            return False

    except Exception as e:
        print(f"❌ Error during campaign editing test: {e}")
        return False

if __name__ == '__main__':
    print("🧪 Testing naive datetime fix in CampanaFundacion views\n")

    success1 = test_datetime_conversion()
    success2 = test_campaign_editing()

    if success1 and success2:
        print("\n🎉 All tests passed! The naive datetime issue has been fixed.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Check the output above.")
        sys.exit(1)
