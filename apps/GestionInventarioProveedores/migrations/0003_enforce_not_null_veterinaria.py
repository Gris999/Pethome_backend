import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("AutenticacionySeguridad", "0008_enforce_not_null_veterinaria"),
        ("GestionInventarioProveedores", "0002_categoriaproducto_veterinaria_producto_veterinaria_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="categoriaproducto",
            name="veterinaria",
            field=models.ForeignKey(
                db_column="id_veterinaria",
                on_delete=django.db.models.deletion.PROTECT,
                related_name="categorias_producto",
                to="AutenticacionySeguridad.veterinaria",
            ),
        ),
        migrations.AlterField(
            model_name="proveedor",
            name="veterinaria",
            field=models.ForeignKey(
                db_column="id_veterinaria",
                on_delete=django.db.models.deletion.PROTECT,
                related_name="proveedores",
                to="AutenticacionySeguridad.veterinaria",
            ),
        ),
        migrations.AlterField(
            model_name="producto",
            name="veterinaria",
            field=models.ForeignKey(
                db_column="id_veterinaria",
                on_delete=django.db.models.deletion.PROTECT,
                related_name="productos",
                to="AutenticacionySeguridad.veterinaria",
            ),
        ),
    ]

