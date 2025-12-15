import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Proyecto.settings')
django.setup()

from App.models import Usuario, Fundacion

def fix_representante():
    print("Fixing representative assignment...")

    # Find representatives
    representantes = Usuario.objects.filter(rol='REPRESENTANTE_FUNDACION')
    print(f"Found {representantes.count()} representatives")

    for rep in representantes:
        print(f"Representative: {rep.nombre} {rep.apellido} - Email: {rep.correo}")
        print(f"  Fundacion asignada: {rep.fundacion_asignada}")

        if rep.fundacion_asignada:
            # Ensure the foundation has this representative
            fundacion = rep.fundacion_asignada
            if fundacion.representante != rep:
                fundacion.representante = rep
                fundacion.save()
                print(f"✅ Set {rep.nombre} as representative of {fundacion.nombre}")
            else:
                print(f"✅ Already correctly assigned")
        else:
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
        if rep.fundacion_asignada and rep.fundacion_asignada.representante == rep:
            print(f"✅ {rep.nombre} correctly assigned to {rep.fundacion_asignada.nombre}")
        else:
            print(f"❌ {rep.nombre} assignment issue")

if __name__ == "__main__":
    fix_representante()
