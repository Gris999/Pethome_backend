import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("AutenticacionySeguridad", "0007_backfill_veterinaria_default"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="veterinaria",
            field=models.ForeignKey(
                db_column="id_veterinaria",
                on_delete=django.db.models.deletion.PROTECT,
                related_name="usuarios",
                to="AutenticacionySeguridad.veterinaria",
            ),
        ),
        migrations.AlterField(
            model_name="grupousuario",
            name="veterinaria",
            field=models.ForeignKey(
                db_column="id_veterinaria",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="grupos_usuario",
                to="AutenticacionySeguridad.veterinaria",
            ),
        ),
        migrations.AlterField(
            model_name="backuprestore",
            name="veterinaria",
            field=models.ForeignKey(
                db_column="id_veterinaria",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="backups_restore",
                to="AutenticacionySeguridad.veterinaria",
            ),
        ),
    ]

