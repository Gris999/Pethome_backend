from django.db import migrations
from django.utils import timezone


def backfill_veterinaria_default(apps, schema_editor):
    Veterinaria = apps.get_model("AutenticacionySeguridad", "Veterinaria")
    PlanSuscripcion = apps.get_model("AutenticacionySeguridad", "PlanSuscripcion")
    Suscripcion = apps.get_model("AutenticacionySeguridad", "Suscripcion")
    User = apps.get_model("AutenticacionySeguridad", "User")
    Bitacora = apps.get_model("AutenticacionySeguridad", "Bitacora")

    Mascota = apps.get_model("GestionClientesyMascotas", "Mascota")
    CategoriaServicio = apps.get_model("GestionServiciosyReserva", "CategoriaServicio")
    Servicio = apps.get_model("GestionServiciosyReserva", "Servicio")
    PrecioServicio = apps.get_model("GestionServiciosyReserva", "PrecioServicio")
    Cita = apps.get_model("GestionServiciosyReserva", "Cita")
    ConsultaClinica = apps.get_model("GestionarClinicaVeterinaria", "ConsultaClinica")
    CategoriaProducto = apps.get_model("GestionInventarioProveedores", "CategoriaProducto")
    Proveedor = apps.get_model("GestionInventarioProveedores", "Proveedor")
    Producto = apps.get_model("GestionInventarioProveedores", "Producto")

    veterinaria, _ = Veterinaria.objects.get_or_create(
        slug="default",
        defaults={
            "nombre": "Veterinaria Default",
            "nit": "N/A",
            "correo": "default@local.invalid",
            "telefono": "",
            "direccion": "",
            "logo": "",
            "estado": True,
        },
    )

    plan, _ = PlanSuscripcion.objects.get_or_create(
        nombre="Plan Default",
        defaults={
            "descripcion": "Plan inicial para migracion",
            "precio_mensual": 0,
            "limite_usuarios": 999999,
            "limite_mascotas": 999999,
            "permite_app_movil": True,
            "permite_reportes": True,
            "permite_backup": True,
            "estado": True,
        },
    )

    Suscripcion.objects.get_or_create(
        veterinaria_id=veterinaria.id_veterinaria,
        plan_id=plan.id_plan,
        defaults={
            "fecha_inicio": timezone.now().date(),
            "fecha_fin": None,
            "estado_suscripcion": "ACTIVA",
            "renovacion_automatica": False,
            "metodo_pago": "MIGRATION",
            "fecha_pago": timezone.now(),
        },
    )

    User.objects.filter(veterinaria__isnull=True).update(veterinaria_id=veterinaria.id_veterinaria)
    Bitacora.objects.filter(veterinaria__isnull=True).update(veterinaria_id=veterinaria.id_veterinaria)

    Mascota.objects.filter(veterinaria__isnull=True).update(veterinaria_id=veterinaria.id_veterinaria)
    CategoriaServicio.objects.filter(veterinaria__isnull=True).update(veterinaria_id=veterinaria.id_veterinaria)
    Servicio.objects.filter(veterinaria__isnull=True).update(veterinaria_id=veterinaria.id_veterinaria)
    PrecioServicio.objects.filter(veterinaria__isnull=True).update(veterinaria_id=veterinaria.id_veterinaria)
    Cita.objects.filter(veterinaria__isnull=True).update(veterinaria_id=veterinaria.id_veterinaria)
    ConsultaClinica.objects.filter(veterinaria__isnull=True).update(veterinaria_id=veterinaria.id_veterinaria)
    CategoriaProducto.objects.filter(veterinaria__isnull=True).update(veterinaria_id=veterinaria.id_veterinaria)
    Proveedor.objects.filter(veterinaria__isnull=True).update(veterinaria_id=veterinaria.id_veterinaria)
    Producto.objects.filter(veterinaria__isnull=True).update(veterinaria_id=veterinaria.id_veterinaria)


def reverse_backfill_veterinaria_default(apps, schema_editor):
    # Reversión segura: no borra datos para evitar pérdida accidental.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("AutenticacionySeguridad", "0006_plansuscripcion_veterinaria_alter_bitacora_options_and_more"),
        ("GestionClientesyMascotas", "0002_mascota_veterinaria"),
        ("GestionInventarioProveedores", "0002_categoriaproducto_veterinaria_producto_veterinaria_and_more"),
        ("GestionServiciosyReserva", "0004_categoriaservicio_veterinaria_cita_veterinaria_and_more"),
        ("GestionarClinicaVeterinaria", "0002_consultaclinica_veterinaria"),
    ]

    operations = [
        migrations.RunPython(backfill_veterinaria_default, reverse_backfill_veterinaria_default),
    ]

