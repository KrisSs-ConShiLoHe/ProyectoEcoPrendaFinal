#!/usr/bin/env python
"""
Script para verificar la configuración de APIs
Ejecución: python test_apis.py
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Proyecto.settings')
django.setup()

from django.conf import settings

# Intentar importar colorama, si no está disponible usar fallback
try:
    from colorama import init, Fore, Style
    HAS_COLORAMA = True
    init(autoreset=True)
except ImportError:
    HAS_COLORAMA = False
    class Fore:
        CYAN = ""
        GREEN = ""
        RED = ""
        YELLOW = ""
    class Style:
        RESET_ALL = ""


def print_section(title):
    """Imprime un título de sección"""
    if HAS_COLORAMA:
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}{title:^60}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    else:
        print(f"\n{'='*60}")
        print(f"{title:^60}")
        print(f"{'='*60}")


def print_success(message):
    """Imprime un mensaje de éxito"""
    if HAS_COLORAMA:
        print(f"{Fore.GREEN}✅ {message}{Style.RESET_ALL}")
    else:
        print(f"✅ {message}")


def print_error(message):
    """Imprime un mensaje de error"""
    if HAS_COLORAMA:
        print(f"{Fore.RED}❌ {message}{Style.RESET_ALL}")
    else:
        print(f"❌ {message}")


def print_warning(message):
    """Imprime un mensaje de advertencia"""
    if HAS_COLORAMA:
        print(f"{Fore.YELLOW}⚠️  {message}{Style.RESET_ALL}")
    else:
        print(f"⚠️  {message}")


def verificar_apis():
    """Verifica que todas las APIs estén configuradas"""
    
    print_section("VERIFICACIÓN DE CONFIGURACIÓN DE APIs - EcoPrenda")
    
    todas_ok = True
    
    # ===== GEOAPIFY =====
    print_section("1️⃣ GEOAPIFY (Mapas)")
    
    if settings.GEOAPIFY_API_KEY:
        print_success("GEOAPIFY_API_KEY configurada")
        print(f"   Valor: {settings.GEOAPIFY_API_KEY[:10]}...{settings.GEOAPIFY_API_KEY[-10:]}")
    else:
        print_error("GEOAPIFY_API_KEY NO configurada")
        todas_ok = False
    
    # ===== CLOUDINARY =====
    print_section("2️⃣ CLOUDINARY (Imágenes)")
    
    required_keys = ['CLOUD_NAME', 'API_KEY', 'API_SECRET']
    cloudinary_ok = True
    
    for key in required_keys:
        val = settings.CLOUDINARY_STORAGE.get(key)
        if val:
            print_success(f"CLOUDINARY_{key} configurada")
            # Mostrar parte de la clave (ofuscada)
            if len(str(val)) > 20:
                print(f"   Valor: {str(val)[:10]}...{str(val)[-10:]}")
            else:
                print(f"   Valor: {val}")
        else:
            print_error(f"CLOUDINARY_{key} NO configurada")
            cloudinary_ok = False
            todas_ok = False
    
    # ===== CLARIFAI =====
    print_section("3️⃣ CLARIFAI (Detección de Prendas)")
    
    if settings.CLARIFAI_PAT:
        print_success("CLARIFAI_PAT configurada")
        print(f"   Valor: {settings.CLARIFAI_PAT[:10]}...{settings.CLARIFAI_PAT[-10:]}")
    else:
        print_error("CLARIFAI_PAT NO configurada")
        todas_ok = False
    
    clarifai_config = [
        ('USER_ID', settings.CLARIFAI_USER_ID),
        ('APP_ID', settings.CLARIFAI_APP_ID),
        ('MODEL_ID', settings.CLARIFAI_MODEL_ID),
        ('MODEL_VERSION_ID', settings.CLARIFAI_MODEL_VERSION_ID),
    ]
    
    for key, val in clarifai_config:
        if val:
            print_success(f"CLARIFAI_{key}: {val}")
        else:
            print_error(f"CLARIFAI_{key} NO configurada")
            todas_ok = False
    
    # ===== LOGGING =====
    print_section("4️⃣ LOGGING")
    
    if 'LOGGING' in dir(settings):
        print_success("Configuración de LOGGING definida")
        log_dir = os.path.join(settings.BASE_DIR, 'logs')
        if not os.path.exists(log_dir):
            print_warning(f"Directorio de logs no existe: {log_dir}")
            print("   ℹ️ Se creará automáticamente al escribir logs")
        else:
            print_success(f"Directorio de logs existe: {log_dir}")
    else:
        print_error("Configuración de LOGGING no definida")
        todas_ok = False
    
    # ===== RESUMEN FINAL =====
    print_section("RESUMEN FINAL")
    
    if todas_ok:
        print_success("✅ TODAS LAS APIs ESTÁN CORRECTAMENTE CONFIGURADAS")
        return 0
    else:
        print_error("❌ ALGUNAS APIs NO ESTÁN CONFIGURADAS")
        print_warning("Por favor, configura las credenciales faltantes en .env")
        return 1


if __name__ == '__main__':
    try:
        exit_code = verificar_apis()
        sys.exit(exit_code)
    except Exception as e:
        print_error(f"Error durante la verificación: {str(e)}")
        sys.exit(1)
