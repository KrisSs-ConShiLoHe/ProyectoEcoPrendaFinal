import re
import os

# Buscar todas las funciones faltantes

# Leer urls.py
with open('App/urls.py', 'r', encoding='utf-8', errors='ignore') as f:
    urls_content = f.read()

# Extraer todas las funciones referenciadas en views.xxx
funcs_in_urls = set(re.findall(r'views\.(\w+)', urls_content))

# Leer todas las funciones en cada módulo
views_dir = 'App/views'
existing_funcs = set()

for filename in os.listdir(views_dir):
    if filename.endswith('.py') and filename not in ['__init__.py', '__pycache__']:
        filepath = os.path.join(views_dir, filename)
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            funcs = set(re.findall(r'^def ([a-z_]\w*)\(', content, re.MULTILINE))
            existing_funcs.update(f for f in funcs if not f.startswith('_'))

# Comparar
missing = funcs_in_urls - existing_funcs
print(f"Funciones en urls.py: {len(funcs_in_urls)}")
print(f"Funciones existentes: {len(existing_funcs)}")
if missing:
    print(f"\nFunciones FALTANTES ({len(missing)}):")
    for func in sorted(missing):
        print(f"  - {func}")
else:
    print("\n✅ Todas las funciones existen!")
