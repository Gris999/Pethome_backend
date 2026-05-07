from django.db import models
from .categoriaservicio import CategoriaServicio

class Servicio(models.Model):
    id_servicio = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    categoria = models.ForeignKey(
        CategoriaServicio,
        on_delete=models.PROTECT,
        db_column="id_categoria",
        related_name="servicios",
    )

    # NUEVOS ATRIBUTOS
    duracion_estimada = models.IntegerField(blank=True, null=True)
    disponible_domicilio = models.BooleanField(default=True)

    estado = models.BooleanField(default=True)
    veterinaria = models.ForeignKey(
        "AutenticacionySeguridad.Veterinaria",
        db_column="id_veterinaria",
        on_delete=models.PROTECT,
        related_name="servicios",
        null=False,
        blank=False,
    )

    class Meta:
        db_table = "servicios"
        verbose_name = "Servicio"
        verbose_name_plural = "Servicios"

    def __str__(self):
        return self.nombre
