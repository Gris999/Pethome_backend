from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from apps.GestionInventarioProveedores.models import Producto
from apps.GestionInventarioProveedores.serializers.producto_serializer import ProductoSerializer


class ProductoListView(generics.ListAPIView):
    serializer_class = ProductoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Producto.objects.filter(
            estado=True,
            veterinaria_id=getattr(self.request.user, "veterinaria_id", None),
        ).order_by("nombre")
