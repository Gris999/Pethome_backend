from django.db import models

class CategoriaServicio(models.Model):
    id_categoria = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    estado = models.BooleanField(default=True)
    veterinaria = models.ForeignKey(
        "AutenticacionySeguridad.Veterinaria",
        db_column="id_veterinaria",
        on_delete=models.PROTECT,
        related_name="categorias_servicio",
        null=False,
        blank=False,
    )

    class Meta:
        db_table = "categorias_servicio"
        verbose_name = "Categoría de Servicio"
        verbose_name_plural = "Categorías de Servicio"

    def __str__(self):
        return self.nombre
