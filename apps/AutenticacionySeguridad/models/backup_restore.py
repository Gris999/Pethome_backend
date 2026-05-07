from django.db import models


class BackupRestore(models.Model):
    TIPOS = [
        ("BACKUP", "Backup"),
        ("RESTORE", "Restore"),
    ]
    ESTADOS = [
        ("INICIADO", "Iniciado"),
        ("EXITOSO", "Exitoso"),
        ("FALLIDO", "Fallido"),
    ]

    id_backup_restore = models.AutoField(primary_key=True)
    tipo = models.CharField(max_length=10, choices=TIPOS)
    fecha_hora = models.DateTimeField(auto_now_add=True)
    ruta_archivo = models.CharField(max_length=500)
    proveedor_almacenamiento = models.CharField(max_length=80, blank=True, null=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default="INICIADO")
    hash_archivo = models.CharField(max_length=255, blank=True, null=True)
    motivo = models.TextField(blank=True, null=True)
    usuario = models.ForeignKey(
        "AutenticacionySeguridad.User",
        db_column="id_usuario",
        on_delete=models.PROTECT,
        related_name="backups_restore",
    )
    veterinaria = models.ForeignKey(
        "AutenticacionySeguridad.Veterinaria",
        db_column="id_veterinaria",
        on_delete=models.CASCADE,
        related_name="backups_restore",
        null=False,
        blank=False,
    )

    class Meta:
        db_table = "backup_restore"
        verbose_name = "Backup restore"
        verbose_name_plural = "Backups restore"
