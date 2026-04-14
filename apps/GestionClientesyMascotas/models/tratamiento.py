from django.db import models

from .historial_clinico import HistorialClinico


class Tratamiento(models.Model):
    class EstadoChoices(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        EN_CURSO = "EN_CURSO", "En curso"
        FINALIZADO = "FINALIZADO", "Finalizado"
        CANCELADO = "CANCELADO", "Cancelado"

    id_tratamiento = models.AutoField(primary_key=True)
    historial_clinico = models.ForeignKey(
        HistorialClinico,
        on_delete=models.CASCADE,
        db_column="id_historial_clinico",
        related_name="tratamientos",
    )
    tipo = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    fecha_ini = models.DateField()
    fecha_fin = models.DateField(blank=True, null=True)
    observacion = models.TextField(blank=True, null=True)
    estado = models.CharField(
        max_length=20,
        choices=EstadoChoices.choices,
        default=EstadoChoices.PENDIENTE,
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tratamiento"
        verbose_name = "Tratamiento"
        verbose_name_plural = "Tratamientos"

    def __str__(self):
        return f"{self.tipo} - {self.historial_clinico.mascota.nombre}"