import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Proyecto.settings')
django.setup()

from App.models import Usuario, Fundacion

def fix_representante():
    print("Fixing representative assignment...")

    # Find representatives without fundacion_asignada
    representantes_sin_asignacion = Usuario.objects.filter(rol='REPRESENTANTE_FUNDACION', fundacion_asignada__isnull=True)
    print(f"Found {representantes_sin_asignacion.count()} representatives without assignment")

    for rep in representantes_sin_asignacion:
        print(f"Representative: {rep.nombre} {rep.apellido} - Email: {rep.correo}")

        # Find foundations without representative
        fundaciones_sin_representante = Fundacion.objects.filter(representante__isnull=True)
        print(f"Found {fundaciones_sin_representante.count()} foundations without representative")

        if fundaciones_sin_representante.exists():
            # Assign the first available foundation
            fundacion = fundaciones_sin_representante.first()
            rep.fundacion_asignada = fundacion
            fundacion.representante = rep
            rep.save()
            fundacion.save()
            print(f"✅ Assigned {rep.nombre} to foundation {fundacion.nombre}")
        else:
            # Create a new foundation
            fundacion = Fundacion.objects.create(
                nombre=f"Fundación de {rep.nombre}",
                descripcion=f"Fundación representada por {rep.nombre} {rep.apellido}",
                activa=True,
                lat=-33.4489,  # Santiago, Chile
                lng=-70.6693
            )
            rep.fundacion_asignada = fundacion
            fundacion.representante = rep
            rep.save()
            fundacion.save()
            print(f"✅ Created new foundation {fundacion.nombre} and assigned to {rep.nombre}")

    # Verify
    representantes = Usuario.objects.filter(rol='REPRESENTANTE_FUNDACION')
    for rep in representantes:
        if rep.fundacion_asignada:
            print(f"✅ {rep.nombre} assigned to {rep.fundacion_asignada.nombre}")
        else:
            print(f"❌ {rep.nombre} still not assigned")

if __name__ == "__main__":
    fix_representante()
