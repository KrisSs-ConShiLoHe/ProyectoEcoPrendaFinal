#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Proyecto.settings')
django.setup()

from App.models import CampanaFundacion

def test_campaigns():
    print("Testing Campaign Data:")
    print(f"Total campaigns: {CampanaFundacion.objects.count()}")

    for campana in CampanaFundacion.objects.all():
        try:
            donadas = campana.prendas_donadas()
            porcentaje = campana.porcentaje_completado()
            print(f"{campana.nombre}: {donadas}/{campana.objetivo_prendas} ({porcentaje:.1f}%)")
        except Exception as e:
            print(f"Error with {campana.nombre}: {e}")

if __name__ == "__main__":
    test_campaigns()
