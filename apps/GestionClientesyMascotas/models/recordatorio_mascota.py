from django.conf import settings
from django.db import models


class RecordatorioMascota(models.Model):
    class TipoRecordatorio(models.TextChoices):
        VACUNA = "VACUNA", "Vacuna"
        DESPARASITACION = "DESPARASITACION", "Desparasitacion"
        MEDICAMENTO = "MEDICAMENTO", "Medicamento"
        CONTROL = "CONTROL", "Control"
        BANIO = "BANIO", "Banio"
        PELUQUERIA = "PELUQUERIA", "Peluqueria"
        OTRO = "OTRO", "Otro"

    class EstadoRecordatorio(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        COMPLETADO = "COMPLETADO", "Completado"
        CANCELADO = "CANCELADO", "Cancelado"
        VENCIDO = "VENCIDO", "Vencido"

    id_recordatorio = models.AutoField(primary_key=True)
    mascota = models.ForeignKey(
        "GestionClientesyMascotas.Mascota",
        db_column="id_mascota",
        on_delete=models.CASCADE,
        related_name="recordatorios",
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        db_column="id_usuario",
        on_delete=models.CASCADE,
        related_name="recordatorios_mascotas",
    )
    veterinaria = models.ForeignKey(
        "AutenticacionySeguridad.Veterinaria",
        db_column="id_veterinaria",
        on_delete=models.PROTECT,
        related_name="recordatorios_mascotas",
    )
    tipo = models.CharField(
        max_length=30,
        choices=TipoRecordatorio.choices,
        default=TipoRecordatorio.OTRO,
    )
    titulo = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True, null=True)
    fecha_programada = models.DateField()
    hora_programada = models.TimeField(blank=True, null=True)
    estado = models.CharField(
        max_length=20,
        choices=EstadoRecordatorio.choices,
        default=EstadoRecordatorio.PENDIENTE,
    )
    notificar = models.BooleanField(default=True)
    dias_anticipacion = models.PositiveIntegerField(default=1)
    notificacion = models.OneToOneField(
        "NotificacionesySeguimiento.Notificacion",
        db_column="id_notificacion",
        on_delete=models.SET_NULL,
        related_name="recordatorio_mascota",
        blank=True,
        null=True,
    )
    fecha_notificacion_enviada = models.DateTimeField(blank=True, null=True)
    intentos_notificacion = models.PositiveSmallIntegerField(default=0)
    ultimo_error_notificacion = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "recordatorio_mascota"
        verbose_name = "Recordatorio de Mascota"
        verbose_name_plural = "Recordatorios de Mascotas"
        indexes = [
            models.Index(
                fields=["veterinaria", "mascota", "estado", "fecha_programada"],
                name="idx_rec_masc_estado",
            ),
        ]

    def __str__(self):
        return f"{self.mascota_id} - {self.titulo}"
