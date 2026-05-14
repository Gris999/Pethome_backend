import os
import sys
from decimal import Decimal

import django
from django.db import transaction

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pethome_back.settings")
os.environ.setdefault("DEBUG", "True")
django.setup()

from apps.AutenticacionySeguridad.models import Veterinaria
from apps.GestionServiciosyReserva.models import CategoriaServicio, PrecioServicio, Servicio


CATALOG = {
    "Consultas PetCare": {
        "descripcion": "Evaluaciones clinicas generales, controles y valoraciones preventivas.",
        "servicios": [
            {
                "nombre": "Consulta General PetCare",
                "descripcion": "Revision clinica completa con anamnesis, examen fisico y recomendaciones.",
                "duracion": 30,
                "domicilio": True,
                "precios": [
                    ("General", "CLINICA", "75.00", "Atencion en consultorio"),
                    ("General", "DOMICILIO", "115.00", "Atencion en domicilio zona urbana"),
                ],
            },
            {
                "nombre": "Control Postoperatorio PetCare",
                "descripcion": "Seguimiento de evolucion y curacion luego de procedimiento quirurgico.",
                "duracion": 25,
                "domicilio": False,
                "precios": [
                    ("General", "CLINICA", "65.00", "Control de evolucion y puntos"),
                ],
            },
            {
                "nombre": "Evaluacion Geriatrica PetCare",
                "descripcion": "Consulta integral para pacientes senior con enfoque preventivo.",
                "duracion": 40,
                "domicilio": False,
                "precios": [
                    ("General", "CLINICA", "130.00", "Chequeo senior en clinica"),
                ],
            },
        ],
    },
    "Vacunacion PetCare": {
        "descripcion": "Inmunizacion preventiva para caninos y felinos en clinica o domicilio.",
        "servicios": [
            {
                "nombre": "Vacunacion Canina PetCare",
                "descripcion": "Aplicacion de esquema vacunal canino segun edad y cartilla.",
                "duracion": 20,
                "domicilio": True,
                "precios": [
                    ("General", "CLINICA", "60.00", "Aplicacion en consultorio"),
                    ("General", "DOMICILIO", "100.00", "Aplicacion en domicilio zona urbana"),
                ],
            },
            {
                "nombre": "Vacunacion Felina PetCare",
                "descripcion": "Aplicacion de esquema vacunal felino con control posterior.",
                "duracion": 20,
                "domicilio": True,
                "precios": [
                    ("General", "CLINICA", "60.00", "Aplicacion en consultorio"),
                    ("General", "DOMICILIO", "100.00", "Aplicacion en domicilio zona urbana"),
                ],
            },
        ],
    },
    "Procedimientos PetCare": {
        "descripcion": "Procedimientos ambulatorios y atenciones de complejidad baja a media.",
        "servicios": [
            {
                "nombre": "Curacion de Heridas PetCare",
                "descripcion": "Limpieza, desinfeccion y vendaje de heridas superficiales o profundas.",
                "duracion": 35,
                "domicilio": True,
                "precios": [
                    ("Simple", "CLINICA", "85.00", "Curacion simple en clinica"),
                    ("Compleja", "CLINICA", "140.00", "Curacion compleja en clinica"),
                    ("Simple", "DOMICILIO", "125.00", "Curacion simple a domicilio"),
                    ("Compleja", "DOMICILIO", "180.00", "Curacion compleja a domicilio"),
                ],
            },
            {
                "nombre": "Retiro de Puntos PetCare",
                "descripcion": "Extraccion de puntos con revision de cicatrizacion.",
                "duracion": 20,
                "domicilio": True,
                "precios": [
                    ("General", "CLINICA", "55.00", "Retiro de puntos en clinica"),
                    ("General", "DOMICILIO", "95.00", "Retiro de puntos a domicilio"),
                ],
            },
        ],
    },
    "Prevencion PetCare": {
        "descripcion": "Servicios enfocados en prevencion de parasitos y control sanitario periodico.",
        "servicios": [
            {
                "nombre": "Desparasitacion Interna PetCare",
                "descripcion": "Administracion de antiparasitarios internos segun peso de la mascota.",
                "duracion": 15,
                "domicilio": True,
                "precios": [
                    ("Pequeno", "CLINICA", "35.00", "Mascota pequena en clinica"),
                    ("Mediano", "CLINICA", "45.00", "Mascota mediana en clinica"),
                    ("Grande", "CLINICA", "55.00", "Mascota grande en clinica"),
                    ("Pequeno", "DOMICILIO", "75.00", "Mascota pequena a domicilio"),
                    ("Mediano", "DOMICILIO", "85.00", "Mascota mediana a domicilio"),
                    ("Grande", "DOMICILIO", "95.00", "Mascota grande a domicilio"),
                ],
            },
            {
                "nombre": "Desparasitacion Externa PetCare",
                "descripcion": "Control de pulgas y garrapatas con productos topicos recomendados.",
                "duracion": 20,
                "domicilio": True,
                "precios": [
                    ("Pequeno", "CLINICA", "45.00", "Aplicacion topica en clinica"),
                    ("Mediano", "CLINICA", "55.00", "Aplicacion topica en clinica"),
                    ("Grande", "CLINICA", "65.00", "Aplicacion topica en clinica"),
                    ("Pequeno", "DOMICILIO", "85.00", "Aplicacion topica a domicilio"),
                    ("Mediano", "DOMICILIO", "95.00", "Aplicacion topica a domicilio"),
                    ("Grande", "DOMICILIO", "105.00", "Aplicacion topica a domicilio"),
                ],
            },
        ],
    },
    "Bienestar PetCare": {
        "descripcion": "Atenciones de cuidado general y bienestar para mejorar calidad de vida.",
        "servicios": [
            {
                "nombre": "Corte de Unas PetCare",
                "descripcion": "Corte seguro de unas con recomendaciones de cuidado en casa.",
                "duracion": 15,
                "domicilio": True,
                "precios": [
                    ("General", "CLINICA", "30.00", "Atencion de corte en clinica"),
                    ("General", "DOMICILIO", "70.00", "Atencion de corte a domicilio"),
                ],
            },
            {
                "nombre": "Limpieza de Oidos PetCare",
                "descripcion": "Limpieza preventiva de conducto auditivo externo y control de olor.",
                "duracion": 20,
                "domicilio": True,
                "precios": [
                    ("General", "CLINICA", "45.00", "Limpieza en clinica"),
                    ("General", "DOMICILIO", "85.00", "Limpieza a domicilio"),
                ],
            },
        ],
    },
    "Documentacion PetCare": {
        "descripcion": "Emision de constancias medicas y documentos sanitarios para traslado.",
        "servicios": [
            {
                "nombre": "Certificado de Viaje PetCare",
                "descripcion": "Evaluacion y emision de certificado sanitario para viaje nacional.",
                "duracion": 30,
                "domicilio": False,
                "precios": [
                    ("General", "CLINICA", "110.00", "Emision de certificado en clinica"),
                ],
            },
        ],
    },
}


def main() -> None:
    vet = Veterinaria.objects.get(slug="petcare")

    created = {"cat": 0, "srv": 0, "prc": 0}
    updated = {"cat": 0, "srv": 0, "prc": 0}

    with transaction.atomic():
        for cat_name, cat_data in CATALOG.items():
            categoria, cat_created = CategoriaServicio.objects.update_or_create(
                nombre=cat_name,
                defaults={
                    "descripcion": cat_data["descripcion"],
                    "estado": True,
                    "veterinaria": vet,
                },
            )
            created["cat"] += int(cat_created)
            updated["cat"] += int(not cat_created)

            for srv_data in cat_data["servicios"]:
                servicio, srv_created = Servicio.objects.update_or_create(
                    nombre=srv_data["nombre"],
                    defaults={
                        "descripcion": srv_data["descripcion"],
                        "categoria": categoria,
                        "duracion_estimada": srv_data["duracion"],
                        "disponible_domicilio": srv_data["domicilio"],
                        "estado": True,
                        "veterinaria": vet,
                    },
                )
                created["srv"] += int(srv_created)
                updated["srv"] += int(not srv_created)

                for variacion, modalidad, precio, descripcion in srv_data["precios"]:
                    _, prc_created = PrecioServicio.objects.update_or_create(
                        servicio=servicio,
                        variacion=variacion,
                        modalidad=modalidad,
                        veterinaria=vet,
                        defaults={
                            "precio": Decimal(precio),
                            "descripcion": descripcion,
                            "estado": True,
                        },
                    )
                    created["prc"] += int(prc_created)
                    updated["prc"] += int(not prc_created)

        CategoriaServicio.objects.filter(
            veterinaria=vet, descripcion__isnull=True
        ).update(descripcion="Categoria de servicios de PetCare", estado=True)
        Servicio.objects.filter(veterinaria=vet, descripcion__isnull=True).update(
            descripcion="Servicio clinico PetCare",
            estado=True,
            duracion_estimada=30,
            disponible_domicilio=False,
        )
        PrecioServicio.objects.filter(veterinaria=vet, descripcion__isnull=True).update(
            descripcion="Tarifa PetCare", estado=True
        )
        PrecioServicio.objects.filter(veterinaria=vet, modalidad__isnull=True).update(
            modalidad="CLINICA"
        )

    totals = {
        "categorias": CategoriaServicio.objects.filter(veterinaria=vet).count(),
        "servicios": Servicio.objects.filter(veterinaria=vet).count(),
        "precios": PrecioServicio.objects.filter(veterinaria=vet).count(),
    }
    print({"created": created, "updated": updated, "totals_petcare": totals})


if __name__ == "__main__":
    main()
