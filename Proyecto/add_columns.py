import os
import sys
import django
# hola xd
# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Proyecto.settings')

# Setup Django
django.setup()

from django.db import connection

def add_missing_columns():
    """Add missing columns to the usuario table."""
    with connection.cursor() as cursor:
        # Add direccion column
        try:
            cursor.execute("""
                ALTER TABLE usuario
                ADD COLUMN IF NOT EXISTS direccion VARCHAR(255) NULL;
            """)
            print("Added 'direccion' column to usuario table.")
        except Exception as e:
            print(f"Error adding 'direccion' column: {e}")

        # Add lat column
        try:
            cursor.execute("""
                ALTER TABLE usuario
                ADD COLUMN IF NOT EXISTS lat DOUBLE PRECISION NULL;
            """)
            print("Added 'lat' column to usuario table.")
        except Exception as e:
            print(f"Error adding 'lat' column: {e}")

        # Add lng column
        try:
            cursor.execute("""
                ALTER TABLE usuario
                ADD COLUMN IF NOT EXISTS lng DOUBLE PRECISION NULL;
            """)
            print("Added 'lng' column to usuario table.")
        except Exception as e:
            print(f"Error adding 'lng' column: {e}")

        # Add mostrar_en_mapa column
        try:
            cursor.execute("""
                ALTER TABLE usuario
                ADD COLUMN IF NOT EXISTS mostrar_en_mapa BOOLEAN DEFAULT FALSE;
            """)
            print("Added 'mostrar_en_mapa' column to usuario table.")
        except Exception as e:
            print(f"Error adding 'mostrar_en_mapa' column: {e}")

    print("All missing columns have been added to the usuario table.")

if __name__ == '__main__':
    add_missing_columns()
