from rest_framework import serializers

from apps.GestionInventarioProveedores.models import ProductoFavorito
from apps.GestionInventarioProveedores.serializers.producto_serializer import ProductoSerializer


class ProductoFavoritoSerializer(serializers.ModelSerializer):
    producto = ProductoSerializer(read_only=True)

    class Meta:
        model = ProductoFavorito
        fields = [
            "id_favorito",
            "producto",
            "fecha_creacion",
        ]
        read_only_fields = fields


class ProductoFavoritoCreateSerializer(serializers.Serializer):
    id_producto = serializers.IntegerField(min_value=1)
