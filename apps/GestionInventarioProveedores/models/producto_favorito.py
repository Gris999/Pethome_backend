from django.conf import settings
from django.db import models


class ProductoFavorito(models.Model):
    id_favorito = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        db_column="id_usuario",
        on_delete=models.CASCADE,
        related_name="productos_favoritos",
    )
    producto = models.ForeignKey(
        "GestionInventarioProveedores.Producto",
        db_column="id_producto",
        on_delete=models.CASCADE,
        related_name="favoritos",
    )
    veterinaria = models.ForeignKey(
        "AutenticacionySeguridad.Veterinaria",
        db_column="id_veterinaria",
        on_delete=models.PROTECT,
        related_name="productos_favoritos",
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "producto_favorito"
        verbose_name = "Producto Favorito"
        verbose_name_plural = "Productos Favoritos"
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "producto", "veterinaria"],
                name="uq_producto_favorito_usuario_producto_veterinaria",
            )
        ]

    def __str__(self):
        return f"{self.usuario_id} - {self.producto_id}"
