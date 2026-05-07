import json

import django.db.models.deletion
from django.db import migrations, models


def backfill_payload(apps, schema_editor):
    Bitacora = apps.get_model("AutenticacionySeguridad", "Bitacora")
    qs = Bitacora.objects.filter(payload__isnull=True)

    for item in qs.iterator():
        data = {
            "accion": getattr(item, "accion", ""),
            "descripcion": getattr(item, "descripcion", ""),
            "ip": getattr(item, "ip", ""),
            "user_agent": getattr(item, "user_agent", ""),
            "modulo": getattr(item, "modulo", ""),
            "entidad_tipo": getattr(item, "entidad_tipo", ""),
            "entidad_id": getattr(item, "entidad_id", ""),
            "resultado": getattr(item, "resultado", ""),
            "metadatos": getattr(item, "metadatos", {}) or {},
            "id_usuario": getattr(item, "usuario_id", None),
        }
        item.payload = json.dumps(data, default=str, ensure_ascii=False).encode("utf-8")
        item.save(update_fields=["payload"])


class Migration(migrations.Migration):

    dependencies = [
        ("AutenticacionySeguridad", "0008_enforce_not_null_veterinaria"),
    ]

    operations = [
        migrations.RunPython(backfill_payload, migrations.RunPython.noop),
        migrations.AlterModelOptions(
            name="bitacora",
            options={
                "ordering": ["-fecha_hora"],
                "verbose_name": "Bitacora",
                "verbose_name_plural": "Bitacora",
            },
        ),
        migrations.AlterField(
            model_name="bitacora",
            name="payload",
            field=models.BinaryField(),
        ),
        migrations.AlterField(
            model_name="bitacora",
            name="veterinaria",
            field=models.ForeignKey(
                blank=True,
                db_column="id_veterinaria",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="bitacoras",
                to="AutenticacionySeguridad.veterinaria",
            ),
        ),
        migrations.RemoveField(
            model_name="bitacora",
            name="accion",
        ),
        migrations.RemoveField(
            model_name="bitacora",
            name="descripcion",
        ),
        migrations.RemoveField(
            model_name="bitacora",
            name="entidad_id",
        ),
        migrations.RemoveField(
            model_name="bitacora",
            name="entidad_tipo",
        ),
        migrations.RemoveField(
            model_name="bitacora",
            name="ip",
        ),
        migrations.RemoveField(
            model_name="bitacora",
            name="metadatos",
        ),
        migrations.RemoveField(
            model_name="bitacora",
            name="modulo",
        ),
        migrations.RemoveField(
            model_name="bitacora",
            name="resultado",
        ),
        migrations.RemoveField(
            model_name="bitacora",
            name="user_agent",
        ),
        migrations.RemoveField(
            model_name="bitacora",
            name="usuario",
        ),
        migrations.RemoveIndex(
            model_name="bitacora",
            name="bitacora_fecha_h_979090_idx",
        ),
        migrations.RemoveIndex(
            model_name="bitacora",
            name="bitacora_accion_401835_idx",
        ),
        migrations.RemoveIndex(
            model_name="bitacora",
            name="bitacora_resulta_f6806c_idx",
        ),
        migrations.RemoveIndex(
            model_name="bitacora",
            name="bitacora_modulo_298c06_idx",
        ),
        migrations.RemoveIndex(
            model_name="bitacora",
            name="bitacora_id_usua_4e574c_idx",
        ),
        migrations.RemoveIndex(
            model_name="bitacora",
            name="bitacora_entidad_d34b25_idx",
        ),
        migrations.AddIndex(
            model_name="bitacora",
            index=models.Index(fields=["veterinaria", "-fecha_hora"], name="idx_bitacora_vet_fecha"),
        ),
        migrations.RunSQL(
            sql=(
                "CREATE INDEX IF NOT EXISTS idx_bitacora_global "
                "ON bitacora(fecha_hora DESC) WHERE id_veterinaria IS NULL;"
            ),
            reverse_sql="DROP INDEX IF EXISTS idx_bitacora_global;",
        ),
    ]

