import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("AutenticacionySeguridad", "0008_enforce_not_null_veterinaria"),
        ("GestionarClinicaVeterinaria", "0002_consultaclinica_veterinaria"),
    ]

    operations = [
        migrations.AlterField(
            model_name="consultaclinica",
            name="veterinaria",
            field=models.ForeignKey(
                db_column="id_veterinaria",
                on_delete=django.db.models.deletion.PROTECT,
                related_name="consultas_clinicas",
                to="AutenticacionySeguridad.veterinaria",
            ),
        ),
    ]

