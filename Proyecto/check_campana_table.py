import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Proyecto.settings')
django.setup()

from django.db import connection

def check_campana_table():
    with connection.cursor() as cursor:
        # Check if table exists (PostgreSQL)
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'campana_fundacion';")
        table_exists = cursor.fetchone()
        print(f"Tabla campana_fundacion existe: {table_exists is not None}")

        if table_exists:
            # Check columns (PostgreSQL)
            cursor.execute("SELECT column_name, data_type, is_nullable, column_default FROM information_schema.columns WHERE table_name = 'campana_fundacion' ORDER BY ordinal_position;")
            columns = cursor.fetchall()
            print("Columnas de campana_fundacion:")
            for col in columns:
                print(f"  {col}")

            # Check data
            cursor.execute("SELECT COUNT(*) FROM campana_fundacion;")
            count = cursor.fetchone()[0]
            print(f"Registros en campana_fundacion: {count}")

if __name__ == "__main__":
    check_campana_table()
