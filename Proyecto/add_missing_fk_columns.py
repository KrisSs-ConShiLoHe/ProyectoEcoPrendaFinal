import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Proyecto.settings')

# Setup Django
django.setup()

from django.db import connection

def add_missing_fk_columns():
    """Add missing foreign key columns to the tables."""
    with connection.cursor() as cursor:
        # Add id column to tipo_transaccion table
        try:
            cursor.execute("""
                ALTER TABLE tipo_transaccion
                ADD COLUMN IF NOT EXISTS id SERIAL PRIMARY KEY;
            """)
            print("Added 'id' column to tipo_transaccion table.")
        except Exception as e:
            print(f"Error adding 'id' column to tipo_transaccion: {e}")

        # Add id column to campana_fundacion table
        try:
            cursor.execute("""
                ALTER TABLE campana_fundacion
                ADD COLUMN IF NOT EXISTS id BIGSERIAL PRIMARY KEY;
            """)
            print("Added 'id' column to campana_fundacion table.")
        except Exception as e:
            print(f"Error adding 'id' column to campana_fundacion: {e}")

        # Add user_id to prenda table
        try:
            cursor.execute("""
                ALTER TABLE prenda
                ADD COLUMN IF NOT EXISTS user_id INTEGER NULL REFERENCES usuario(id_usuario);
            """)
            print("Added 'user_id' column to prenda table.")
        except Exception as e:
            print(f"Error adding 'user_id' column to prenda: {e}")

        # Add prenda_id to transaccion table
        try:
            cursor.execute("""
                ALTER TABLE transaccion
                ADD COLUMN IF NOT EXISTS prenda_id INTEGER NULL REFERENCES prenda(id_prenda);
            """)
            print("Added 'prenda_id' column to transaccion table.")
        except Exception as e:
            print(f"Error adding 'prenda_id' column to transaccion: {e}")

        # Add tipo_id to transaccion table
        try:
            cursor.execute("""
                ALTER TABLE transaccion
                ADD COLUMN IF NOT EXISTS tipo_id INTEGER NULL REFERENCES tipo_transaccion(id);
            """)
            print("Added 'tipo_id' column to transaccion table.")
        except Exception as e:
            print(f"Error adding 'tipo_id' column to transaccion: {e}")

        # Add fundacion_id to transaccion table
        try:
            cursor.execute("""
                ALTER TABLE transaccion
                ADD COLUMN IF NOT EXISTS fundacion_id INTEGER NULL REFERENCES fundacion(id_fundacion);
            """)
            print("Added 'fundacion_id' column to transaccion table.")
        except Exception as e:
            print(f"Error adding 'fundacion_id' column to transaccion: {e}")

        # Add campana_id to transaccion table
        try:
            cursor.execute("""
                ALTER TABLE transaccion
                ADD COLUMN IF NOT EXISTS campana_id INTEGER NULL REFERENCES campana_fundacion(id);
            """)
            print("Added 'campana_id' column to transaccion table.")
        except Exception as e:
            print(f"Error adding 'campana_id' column to transaccion: {e}")

        # Add fundacion_id to campana_fundacion table
        try:
            cursor.execute("""
                ALTER TABLE campana_fundacion
                ADD COLUMN IF NOT EXISTS fundacion_id INTEGER NULL REFERENCES fundacion(id_fundacion);
            """)
            print("Added 'fundacion_id' column to campana_fundacion table.")
        except Exception as e:
            print(f"Error adding 'fundacion_id' column to campana_fundacion: {e}")

        # Add emisor_id to mensaje table
        try:
            cursor.execute("""
                ALTER TABLE mensaje
                ADD COLUMN IF NOT EXISTS emisor_id INTEGER NULL REFERENCES usuario(id_usuario);
            """)
            print("Added 'emisor_id' column to mensaje table.")
        except Exception as e:
            print(f"Error adding 'emisor_id' column to mensaje: {e}")

        # Add receptor_id to mensaje table
        try:
            cursor.execute("""
                ALTER TABLE mensaje
                ADD COLUMN IF NOT EXISTS receptor_id INTEGER NULL REFERENCES usuario(id_usuario);
            """)
            print("Added 'receptor_id' column to mensaje table.")
        except Exception as e:
            print(f"Error adding 'receptor_id' column to mensaje: {e}")

    print("All missing foreign key columns have been added.")

if __name__ == '__main__':
    add_missing_fk_columns()
