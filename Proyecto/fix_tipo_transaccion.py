import os
import django
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Proyecto.settings')
django.setup()

from django.db import connection

def fix_tipo_transaccion():
    with connection.cursor() as cursor:
        # Verificar si la tabla existe (PostgreSQL)
        cursor.execute("SELECT tablename FROM pg_tables WHERE tablename = 'tipo_transaccion';")
        table_exists = cursor.fetchone()

        if table_exists:
            # Verificar si la columna id existe
            cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'tipo_transaccion' AND column_name = 'id';")
            id_exists = cursor.fetchone()

            if not id_exists:
                print("Adding id column to tipo_transaccion table...")
                # Primero, crear una nueva tabla temporal con el esquema correcto
                cursor.execute("""
                    CREATE TABLE tipo_transaccion_temp (
                        id SERIAL PRIMARY KEY,
                        nombre_tipo VARCHAR(50) NOT NULL,
                        descripcion VARCHAR(200)
                    );
                """)

                # Copiar datos existentes
                cursor.execute("INSERT INTO tipo_transaccion_temp (nombre_tipo, descripcion) SELECT nombre_tipo, descripcion FROM tipo_transaccion;")

                # Eliminar tabla original y renombrar temporal
                cursor.execute("DROP TABLE tipo_transaccion CASCADE;")
                cursor.execute("ALTER TABLE tipo_transaccion_temp RENAME TO tipo_transaccion;")

                print("id column added successfully.")
            else:
                print("id column already exists.")

            # Verificar si hay datos
            cursor.execute("SELECT COUNT(*) FROM tipo_transaccion;")
            count = cursor.fetchone()[0]
            if count == 0:
                print("Inserting default transaction types...")
                tipos = [
                    ('Donación', 'Donación de prenda a fundación'),
                    ('Venta', 'Venta de prenda entre usuarios'),
                    ('Intercambio', 'Intercambio de prendas entre usuarios'),
                ]
                for nombre, desc in tipos:
                    cursor.execute("INSERT INTO tipo_transaccion (nombre_tipo, descripcion) VALUES (%s, %s);", (nombre, desc))
            else:
                print(f"Table already has {count} records.")
        else:
            # Crear la tabla si no existe
            print("Creating tipo_transaccion table with correct schema...")
            cursor.execute("""
                CREATE TABLE tipo_transaccion (
                    id SERIAL PRIMARY KEY,
                    nombre_tipo VARCHAR(50) NOT NULL,
                    descripcion VARCHAR(200)
                );
            """)

            # Insertar tipos de transacción por defecto
            print("Inserting default transaction types...")
            tipos = [
                ('Donación', 'Donación de prenda a fundación'),
                ('Venta', 'Venta de prenda entre usuarios'),
                ('Intercambio', 'Intercambio de prendas entre usuarios'),
            ]
            for nombre, desc in tipos:
                cursor.execute("INSERT INTO tipo_transaccion (nombre_tipo, descripcion) VALUES (%s, %s);", (nombre, desc))

        print("tipo_transaccion table fixed successfully.")

if __name__ == "__main__":
    fix_tipo_transaccion()
