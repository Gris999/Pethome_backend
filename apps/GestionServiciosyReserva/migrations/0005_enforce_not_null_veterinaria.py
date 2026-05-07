import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("AutenticacionySeguridad", "0008_enforce_not_null_veterinaria"),
        ("GestionServiciosyReserva", "0004_categoriaservicio_veterinaria_cita_veterinaria_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="categoriaservicio",
            name="veterinaria",
            field=models.ForeignKey(
                db_column="id_veterinaria",
                on_delete=django.db.models.deletion.PROTECT,
                related_name="categorias_servicio",
                to="AutenticacionySeguridad.veterinaria",
            ),
        ),
        migrations.AlterField(
            model_name="servicio",
            name="veterinaria",
            field=models.ForeignKey(
                db_column="id_veterinaria",
                on_delete=django.db.models.deletion.PROTECT,
                related_name="servicios",
                to="AutenticacionySeguridad.veterinaria",
            ),
        ),
        migrations.AlterField(
            model_name="precioservicio",
            name="veterinaria",
            field=models.ForeignKey(
                db_column="id_veterinaria",
                on_delete=django.db.models.deletion.PROTECT,
                related_name="precios_servicio",
                to="AutenticacionySeguridad.veterinaria",
            ),
        ),
        migrations.AlterField(
            model_name="cita",
            name="veterinaria",
            field=models.ForeignKey(
                db_column="id_veterinaria",
                on_delete=django.db.models.deletion.PROTECT,
                related_name="citas",
                to="AutenticacionySeguridad.veterinaria",
            ),
        ),
    ]

