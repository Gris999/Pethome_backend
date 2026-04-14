from django.db import models

from .mascota import Mascota


class HistorialClinico(models.Model):
    class EstadoChoices(models.TextChoices):
        ACTIVO = "ACTIVO", "Activo"
        INACTIVO = "INACTIVO", "Inactivo"
        ARCHIVADO = "ARCHIVADO", "Archivado"

    id_historial_clinico = models.AutoField(primary_key=True)
    mascota = models.OneToOneField(
        Mascota,
        on_delete=models.CASCADE,
        db_column="id_mascota",
        related_name="historial_clinico",
    )
    observaciones_generales = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    estado = models.CharField(
        max_length=20,
        choices=EstadoChoices.choices,
        default=EstadoChoices.ACTIVO,
    )

    class Meta:
        db_table = "historial_clinico"
        verbose_name = "Historial Clínico"
        verbose_name_plural = "Historiales Clínicos"

    def __str__(self):
        return f"Historial de {self.mascota.nombre}"
from django.db import models

from apps.GestionClientesyMascotas.models import Mascota


class HistorialClinico(models.Model):
    id_historial_clinico = models.AutoField(primary_key=True)
    mascota = models.ForeignKey(
        Mascota,
        on_delete=models.CASCADE,
        db_column="id_mascota",
        related_name="historiales_clinicos",
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "historial_clinico"
        verbose_name = "Historial clínico"
        verbose_name_plural = "Historiales clínicos"

    def __str__(self):
        return f"Historial de {self.mascota.nombre}"