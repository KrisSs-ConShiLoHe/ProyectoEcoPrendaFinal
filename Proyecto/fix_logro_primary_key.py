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

def fix_logro_primary_key():
    """Fix the primary key issue in the logro table."""
    with connection.cursor() as cursor:
        # Check if 'id' column exists and is primary key
        cursor.execute("""
            SELECT column_name, is_nullable, data_type
            FROM information_schema.columns
            WHERE table_name = 'logro' AND column_name = 'id';
        """)
        id_column = cursor.fetchone()
        if id_column:
            print("Found 'id' column in logro table.")
            # Check if 'id' is primary key
            cursor.execute("""
                SELECT constraint_name
                FROM information_schema.table_constraints
                WHERE table_name = 'logro' AND constraint_type = 'PRIMARY KEY';
            """)
            pk_constraints = cursor.fetchall()
            if pk_constraints:
                print(f"Primary key constraints: {pk_constraints}")
                # If there are multiple, drop the one on 'id'
                for constraint in pk_constraints:
                    constraint_name = constraint[0]
                    if 'id' in constraint_name.lower():
                        try:
                            cursor.execute(f"ALTER TABLE logro DROP CONSTRAINT {constraint_name};")
                            print(f"Dropped primary key constraint {constraint_name} on 'id'.")
                        except Exception as e:
                            print(f"Error dropping constraint {constraint_name}: {e}")
            # Now, drop the 'id' column if it exists
            try:
                cursor.execute("ALTER TABLE logro DROP COLUMN IF EXISTS id;")
                print("Dropped 'id' column from logro table.")
            except Exception as e:
                print(f"Error dropping 'id' column: {e}")
        else:
            print("No 'id' column found in logro table.")

        # Ensure 'codigo' is primary key
        try:
            cursor.execute("ALTER TABLE logro ADD PRIMARY KEY (codigo);")
            print("Set 'codigo' as primary key for logro table.")
        except Exception as e:
            print(f"Error setting 'codigo' as primary key: {e}")

if __name__ == '__main__':
    fix_logro_primary_key()
