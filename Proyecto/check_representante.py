import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Proyecto.settings')
django.setup()

from App.models import Usuario, Fundacion

def check_representante():
    print("Checking representative user...")

    # Find representative users
    representantes = Usuario.objects.filter(rol='REPRESENTANTE_FUNDACION')
    print(f"Found {representantes.count()} representative users")

    for rep in representantes:
        print(f"Representative: {rep.nombre} {rep.apellido} - Email: {rep.correo}")
        print(f"  Fundacion asignada: {rep.fundacion_asignada}")
        if rep.fundacion_asignada:
            print(f"  Fundacion name: {rep.fundacion_asignada.nombre}")
        else:
            print("  ❌ No fundacion asignada!")

    # Check foundations
    fundaciones = Fundacion.objects.all()
    print(f"\nFound {fundaciones.count()} foundations")
    for fund in fundaciones:
        print(f"Foundation: {fund.nombre} - ID: {fund.id_fundacion}")
        print(f"  Representante: {fund.representante}")
        if fund.representante:
            print(f"  Representante name: {fund.representante.nombre}")

if __name__ == "__main__":
    check_representante()
