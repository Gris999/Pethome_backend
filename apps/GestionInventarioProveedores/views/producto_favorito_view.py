from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.AutenticacionySeguridad.mixins.tenant_mixins import TenantViewMixin
from apps.GestionInventarioProveedores.models import Producto, ProductoFavorito
from apps.GestionInventarioProveedores.serializers.producto_favorito_serializer import (
    ProductoFavoritoCreateSerializer,
    ProductoFavoritoSerializer,
)


class ProductoFavoritoListCreateView(TenantViewMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        tenant_id = self.get_tenant_id()
        if not tenant_id:
            return ProductoFavorito.objects.none()
        return (
            ProductoFavorito.objects.select_related(
                "producto",
                "producto__categoria_producto",
                "producto__proveedor",
                "producto__veterinaria",
            )
            .filter(
                usuario=self.request.user,
                veterinaria_id=tenant_id,
                producto__estado=True,
                producto__visible_catalogo=True,
            )
            .order_by("-fecha_creacion")
        )

    def get(self, request):
        serializer = ProductoFavoritoSerializer(
            self.get_queryset(),
            many=True,
            context={"request": request},
        )
        return Response(serializer.data)

    def post(self, request):
        tenant_id = self.get_tenant_id()
        if not tenant_id:
            raise ValidationError({"detail": "No se pudo resolver la veterinaria actual."})

        serializer = ProductoFavoritoCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        producto_id = serializer.validated_data["id_producto"]

        producto = Producto.objects.filter(
            id_producto=producto_id,
            veterinaria_id=tenant_id,
            estado=True,
            visible_catalogo=True,
        ).first()
        if producto is None:
            raise NotFound("Producto no encontrado o no disponible en catalogo.")

        favorito, _ = ProductoFavorito.objects.get_or_create(
            usuario=request.user,
            producto=producto,
            veterinaria_id=tenant_id,
        )
        output = ProductoFavoritoSerializer(
            favorito,
            context={"request": request},
        )
        return Response(output.data, status=status.HTTP_201_CREATED)


class ProductoFavoritoDeleteView(TenantViewMixin, APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, id_producto):
        tenant_id = self.get_tenant_id()
        if not tenant_id:
            raise ValidationError({"detail": "No se pudo resolver la veterinaria actual."})

        ProductoFavorito.objects.filter(
            usuario=request.user,
            producto_id=id_producto,
            veterinaria_id=tenant_id,
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
