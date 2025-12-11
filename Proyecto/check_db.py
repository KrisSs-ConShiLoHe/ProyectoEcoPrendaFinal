import os
import django
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Proyecto.settings')
django.setup()

from django.db import connection

def check_tables():
    with connection.cursor() as cursor:
        # Verificar si la tabla tipo_transaccion existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tipo_transaccion';")
        table_exists = cursor.fetchone()
        print(f"Tabla tipo_transaccion existe: {table_exists is not None}")

        if table_exists:
            # Verificar columnas de tipo_transaccion
            cursor.execute("PRAGMA table_info(tipo_transaccion);")
            columns = cursor.fetchall()
            print("Columnas de tipo_transaccion:")
            for col in columns:
                print(f"  {col}")

            # Verificar si hay datos
            cursor.execute("SELECT COUNT(*) FROM tipo_transaccion;")
            count = cursor.fetchone()[0]
            print(f"Registros en tipo_transaccion: {count}")

        # Verificar tabla transaccion
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='transaccion';")
        trans_exists = cursor.fetchone()
        print(f"Tabla transaccion existe: {trans_exists is not None}")

        if trans_exists:
            cursor.execute("PRAGMA table_info(transaccion);")
            trans_columns = cursor.fetchall()
            print("Columnas de transaccion:")
            for col in trans_columns:
                print(f"  {col}")

if __name__ == "__main__":
    check_tables()
