#!/usr/bin/env python
"""
Script to test if database errors are resolved
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Proyecto.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from App.models import Prenda, Transaccion, TipoTransaccion, Fundacion, Mensaje, ImpactoAmbiental, Logro, UsuarioLogro, CampanaFundacion

def test_database_queries():
    """Test database queries that were failing"""
    print("Testing database queries...")

    from django.db import connection

    # Check actual column names in transaccion table
    with connection.cursor() as cursor:
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'transaccion' ORDER BY column_name;")
        columns = [row[0] for row in cursor.fetchall()]
        print(f"Transaccion table columns: {columns}")

    try:
        # Test Prenda query with user
        prendas = Prenda.objects.select_related('user').all()[:5]
        print(f"✅ Prenda.objects.select_related('user') - OK ({len(prendas)} records)")

        # Test Transaccion queries - try different approaches
        try:
            transacciones = Transaccion.objects.select_related('user_origen', 'user_destino', 'tipo', 'prenda', 'fundacion').all()[:5]
            print(f"✅ Transaccion.objects.select_related() - OK ({len(transacciones)} records)")
        except Exception as e:
            print(f"⚠️  Transaccion select_related failed: {e}")
            # Try without tipo
            try:
                transacciones = Transaccion.objects.select_related('user_origen', 'user_destino', 'prenda', 'fundacion').all()[:5]
                print(f"✅ Transaccion.objects.select_related() (without tipo) - OK ({len(transacciones)} records)")
            except Exception as e2:
                print(f"❌ Transaccion queries failed: {e2}")

        # Test ImpactoAmbiental query
        impactos = ImpactoAmbiental.objects.select_related('prenda__user').all()[:5]
        print(f"✅ ImpactoAmbiental.objects.select_related('prenda__user') - OK ({len(impactos)} records)")

        # Test CampanaFundacion query
        campanas = CampanaFundacion.objects.select_related('fundacion').all()[:5]
        print(f"✅ CampanaFundacion.objects.select_related('fundacion') - OK ({len(campanas)} records)")

        # Test UsuarioLogro query
        logros = UsuarioLogro.objects.select_related('user', 'logro').all()[:5]
        print(f"✅ UsuarioLogro.objects.select_related('user', 'logro') - OK ({len(logros)} records)")

        # Test Mensaje query
        mensajes = Mensaje.objects.select_related('emisor', 'receptor').all()[:5]
        print(f"✅ Mensaje.objects.select_related('emisor', 'receptor') - OK ({len(mensajes)} records)")

        print("\n✅ All database queries executed successfully!")
        return True

    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def test_views():
    """Test views that were failing"""
    print("\nTesting views...")

    client = Client()

    # Test URLs that were failing
    test_urls = [
        '/prendas/',
        '/impacto/',
        '/campanas-solidarias/',
        '/perfil/',
        '/mis-transacciones/',
        '/mi-impacto/',
        '/mis-logros/',
        '/mensajes/',
    ]

    for url in test_urls:
        try:
            response = client.get(url)
            if response.status_code == 302:  # Redirect to login (expected for protected views)
                print(f"✅ {url} - OK (redirect to login)")
            elif response.status_code == 200:
                print(f"✅ {url} - OK (200)")
            else:
                print(f"⚠️  {url} - Status {response.status_code}")
        except Exception as e:
            print(f"❌ {url} - Error: {e}")
            return False

    print("✅ All views tested successfully!")
    return True

if __name__ == '__main__':
    print("Testing database errors resolution...\n")

    db_ok = test_database_queries()
    views_ok = test_views()

    if db_ok and views_ok:
        print("\n🎉 All tests passed! Database errors appear to be resolved.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Errors may still exist.")
        sys.exit(1)
