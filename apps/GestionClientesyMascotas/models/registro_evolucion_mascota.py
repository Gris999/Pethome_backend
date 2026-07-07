from django.conf import settings
from django.db import models


class RegistroEvolucionMascota(models.Model):
    class CondicionCorporal(models.TextChoices):
        BAJO = "BAJO", "Bajo peso"
        NORMAL = "NORMAL", "Normal"
        SOBREPESO = "SOBREPESO", "Sobrepeso"
        OBESIDAD = "OBESIDAD", "Obesidad"
        NO_EVALUADO = "NO_EVALUADO", "No evaluado"

    id_registro = models.AutoField(primary_key=True)
    mascota = models.ForeignKey(
        "GestionClientesyMascotas.Mascota",
        db_column="id_mascota",
        on_delete=models.CASCADE,
        related_name="registros_evolucion",
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        db_column="id_usuario",
        on_delete=models.CASCADE,
        related_name="registros_evolucion_mascotas",
    )
    veterinaria = models.ForeignKey(
        "AutenticacionySeguridad.Veterinaria",
        db_column="id_veterinaria",
        on_delete=models.PROTECT,
        related_name="registros_evolucion_mascotas",
    )
    peso = models.DecimalField(max_digits=10, decimal_places=2)
    condicion_corporal = models.CharField(
        max_length=20,
        choices=CondicionCorporal.choices,
        default=CondicionCorporal.NO_EVALUADO,
    )
    nota = models.TextField(blank=True, null=True)
    fecha_registro = models.DateField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "registro_evolucion_mascota"
        ordering = ["-fecha_registro", "-fecha_creacion"]
        indexes = [
            models.Index(fields=["mascota", "fecha_registro"], name="idx_evo_masc_fecha"),
            models.Index(fields=["veterinaria", "fecha_registro"], name="idx_evo_vet_fecha"),
        ]
        verbose_name = "Registro de evolucion de mascota"
        verbose_name_plural = "Registros de evolucion de mascotas"

    def __str__(self):
        return f"{self.mascota.nombre} - {self.peso} kg - {self.fecha_registro}"
