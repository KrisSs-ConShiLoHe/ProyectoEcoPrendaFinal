import os
import re

views_dir = os.path.join(os.getcwd(), 'App', 'views')
modules = {}

# Archivos de módulos
module_files = [
    'cookie.py',
    'auth.py', 
    'prenda.py',
    'transaccion.py',
    'mensaje.py',
    'fundacion.py',
    'logro.py',
    'impacto_ambiental.py',
    'campana.py'
]

for module_file in module_files:
    filepath = os.path.join(views_dir, module_file)
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                # Extraer funciones que no comienzan con _
                functions = re.findall(r'^def ([a-z_]\w*)\(', content, re.MULTILINE)
                functions = [f for f in functions if not f.startswith('_')]
                module_name = module_file.replace('.py', '')
                modules[module_name] = functions
                print(f'{module_name}: {len(functions)} functions')
        except Exception as e:
            print(f'Error in {module_file}: {e}')

# Generate __init__.py content
init_content = "# Importar todas las funciones de los módulos de vistas\n"

for module_name, functions in modules.items():
    if functions:
        funcs_str = ',\n    '.join(functions)
        init_content += f"""
from .{module_name} import (
    {funcs_str},
)
"""

# Add __all__
all_functions = []
for functions in modules.values():
    all_functions.extend(functions)

init_content += f"\n__all__ = [\n"
for func in all_functions:
    init_content += f"    '{func}',\n"
init_content += "]\n"

# Write to file
init_file = os.path.join(views_dir, '__init__.py')
with open(init_file, 'w', encoding='utf-8') as f:
    f.write(init_content)

print(f"\n✅ Generated {init_file}")
print(f"Total functions: {len(all_functions)}")
