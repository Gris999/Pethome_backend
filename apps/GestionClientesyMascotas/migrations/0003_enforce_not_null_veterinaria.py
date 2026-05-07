import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("AutenticacionySeguridad", "0008_enforce_not_null_veterinaria"),
        ("GestionClientesyMascotas", "0002_mascota_veterinaria"),
    ]

    operations = [
        migrations.AlterField(
            model_name="mascota",
            name="veterinaria",
            field=models.ForeignKey(
                db_column="id_veterinaria",
                on_delete=django.db.models.deletion.PROTECT,
                related_name="mascotas",
                to="AutenticacionySeguridad.veterinaria",
            ),
        ),
    ]

