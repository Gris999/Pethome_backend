from django.db import models


class CategoriaServicio(models.Model):
    id_categoria = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    estado = models.BooleanField(default=True)

    class Meta:
        db_table = "categorias_servicio"
        verbose_name = "Categoría de Servicio"
        verbose_name_plural = "Categorías de Servicio"

    def __str__(self):
        return self.nombre
    

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
    estado = models.BooleanField(default=True)

    class Meta:
        db_table = "servicios"
        verbose_name = "Servicio"
        verbose_name_plural = "Servicios"

    def __str__(self):
        return self.nombre
    
class PrecioServicio(models.Model):
    id_precio = models.AutoField(primary_key=True)

    servicio = models.ForeignKey(
        Servicio,
        on_delete=models.CASCADE,
        related_name="precios"
    )

    variacion = models.CharField(max_length=50, default="General")
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    descripcion = models.TextField(blank=True, null=True)
    estado = models.BooleanField(default=True)


    class Meta:
        db_table = "precios_servicio"
        constraints = [
            models.UniqueConstraint(
                fields=["servicio", "variacion"],
                name="unique_variacion_por_servicio"
            )
        ]

    def __str__(self):
        return f"{self.servicio.nombre} - {self.variacion} - {self.precio}"