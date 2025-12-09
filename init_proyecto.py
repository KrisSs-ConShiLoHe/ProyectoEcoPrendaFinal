#!/usr/bin/env python
"""
Script para inicializar el proyecto EcoPrenda
Crea directorios necesarios y verifica configuración
"""

import os
import sys
import shutil
from pathlib import Path

def crear_directorios():
    """Crea directorios necesarios"""
    directorios = [
        'logs',
        'media',
        'staticfiles',
    ]
    
    base_dir = Path(__file__).parent / 'Proyecto'
    
    for dir_name in directorios:
        dir_path = base_dir / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"✅ Directorio creado: {dir_path}")
        else:
            print(f"ℹ️ Directorio ya existe: {dir_path}")


def crear_env_si_no_existe():
    """Crea .env desde .env.example si no existe"""
    base_dir = Path(__file__).parent / 'Proyecto'
    env_file = base_dir / '.env'
    env_example = base_dir / '.env.example'
    
    if env_file.exists():
        print(f"ℹ️ Archivo .env ya existe")
    elif env_example.exists():
        print(f"⚠️ Archivo .env no existe, creando desde .env.example...")
        shutil.copy(str(env_example), str(env_file))
        print(f"✅ Archivo .env creado - LLENA LAS CREDENCIALES")
    else:
        print(f"❌ No se encontró .env.example")


def main():
    """Función principal"""
    print("=" * 60)
    print("INICIALIZACIÓN DEL PROYECTO ECOPRENDA".center(60))
    print("=" * 60)
    print()
    
    print("📁 Creando directorios...")
    crear_directorios()
    print()
    
    print("📝 Verificando archivos de configuración...")
    crear_env_si_no_existe()
    print()
    
    print("=" * 60)
    print("✅ INICIALIZACIÓN COMPLETADA".center(60))
    print("=" * 60)
    print()
    print("PRÓXIMOS PASOS:")
    print("1. Llena el archivo .env con tus credenciales")
    print("2. Ejecuta: python Proyecto/test_apis.py")
    print("3. Ejecuta: python Proyecto/manage.py migrate")
    print("4. Ejecuta: python Proyecto/manage.py runserver")
    print()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)
