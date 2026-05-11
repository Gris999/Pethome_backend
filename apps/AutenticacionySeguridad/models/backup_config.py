from django.db import models


class BackupConfig(models.Model):
    FRECUENCIAS = [
        ("DIARIO", "Diario"),
        ("SEMANAL", "Semanal"),
        ("MENSUAL", "Mensual"),
        ("PERSONALIZADO", "Personalizado"),
    ]

    id_backup_config = models.AutoField(primary_key=True)
    veterinaria = models.OneToOneField(
        "AutenticacionySeguridad.Veterinaria",
        db_column="id_veterinaria",
        on_delete=models.CASCADE,
        related_name="backup_config",
        null=False,
        blank=False,
    )
    frecuencia = models.CharField(
        max_length=20, choices=FRECUENCIAS, default="SEMANAL"
    )
    dias_retención = models.IntegerField(default=30)
    último_backup = models.DateTimeField(null=True, blank=True)
    próximo_backup_programado = models.DateTimeField(null=True, blank=True)
    activo = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "backup_config"
        verbose_name = "Configuración de backup"
        verbose_name_plural = "Configuraciones de backup"

    def __str__(self):
        return f"Backup Config - {self.veterinaria.nombre} ({self.frecuencia})"
