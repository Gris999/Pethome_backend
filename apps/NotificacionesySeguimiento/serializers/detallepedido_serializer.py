from rest_framework import serializers

from ..models import DetallePedido


class DetallePedidoSerializer(serializers.ModelSerializer):
    producto_id = serializers.IntegerField(source="producto.id_producto", read_only=True)
    producto_nombre = serializers.CharField(source="producto.nombre", read_only=True)

    class Meta:
        model = DetallePedido
        fields = [
            "id_detalle_pedido",
            "producto_id",
            "producto_nombre",
            "cantidad",
            "precio_unitario",
            "subtotal",
            "observacion",
            "estado",
        ]
