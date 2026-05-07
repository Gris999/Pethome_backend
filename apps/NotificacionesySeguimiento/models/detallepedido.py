from django.db import models


class DetallePedido(models.Model):
    id_detalle_pedido = models.BigAutoField(primary_key=True)
    pedido = models.ForeignKey(
        "NotificacionesySeguimiento.Pedido",
        on_delete=models.CASCADE,
        related_name="detalles",
    )
    producto = models.ForeignKey(
        "GestionInventarioProveedores.Producto",
        on_delete=models.PROTECT,
        related_name="detalles_pedido",
    )

    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    observacion = models.TextField(null=True, blank=True)
    estado = models.BooleanField(default=True)

    class Meta:
        db_table = "detalle_pedido"

    def __str__(self):
        return f"{self.producto.nombre} x {self.cantidad}"
