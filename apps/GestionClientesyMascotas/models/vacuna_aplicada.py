from django.db import models

from .historial_clinico import HistorialClinico


class VacunaAplicada(models.Model):
    class EstadoChoices(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        APLICADA = "APLICADA", "Aplicada"
        REF = "REF", "Refuerzo"

    id_vacuna_aplicada = models.AutoField(primary_key=True)
    historial_clinico = models.ForeignKey(
        HistorialClinico,
        on_delete=models.CASCADE,
        db_column="id_historial_clinico",
        related_name="vacunas_aplicadas",
    )
    nombre_vacuna = models.CharField(max_length=100)
    dosis = models.CharField(max_length=50, blank=True, null=True)
    fecha_aplicada = models.DateField()
    fecha_proxima = models.DateField(blank=True, null=True)
    observacion = models.TextField(blank=True, null=True)
    estado = models.CharField(
        max_length=20,
        choices=EstadoChoices.choices,
        default=EstadoChoices.APLICADA,
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "vacuna_aplicada"
        verbose_name = "Vacuna Aplicada"
        verbose_name_plural = "Vacunas Aplicadas"

    def __str__(self):
        return f"{self.nombre_vacuna} - {self.historial_clinico.mascota.nombre} ({self.fecha_aplicada})"
