from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.AutenticacionySeguridad.enums.roles import RoleEnum
from apps.GestionClientesyMascotas.models import Mascota
from apps.GestionClientesyMascotas.serializers.mascota_serializer import MascotaSerializer
from apps.GestionInventarioProveedores.serializers.producto_serializer import ProductoSerializer
from apps.GestionInventarioProveedores.services.producto_recomendacion_service import (
    ProductoRecomendacionService,
)


class ProductoRecomendacionMascotaView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        mascota_id = request.query_params.get("mascota_id")
        if not mascota_id:
            return Response(
                {"detail": "Debe enviar mascota_id."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        tenant = getattr(request, "tenant", None)
        tenant_id = getattr(tenant, "id", None) or getattr(
            request.user,
            "veterinaria_id",
            None,
        )
        queryset = Mascota.objects.select_related(
            "usuario",
            "usuario__perfil",
            "veterinaria",
            "especie",
            "raza",
        ).filter(veterinaria_id=tenant_id, estado=True)

        role_name = (getattr(getattr(request.user, "role", None), "nombre", "") or "").upper()
        if role_name == RoleEnum.CLIENT.value:
            queryset = queryset.filter(usuario=request.user)

        mascota = get_object_or_404(queryset, id_mascota=mascota_id)
        recommendations = ProductoRecomendacionService.get_for_pet(
            mascota=mascota,
            tenant_id=tenant_id,
            request=request,
        )
        return Response(
            {
                "mascota": MascotaSerializer(mascota, context={"request": request}).data,
                "recomendaciones": [
                    {
                        "producto": ProductoSerializer(
                            item["producto"],
                            context={"request": request},
                        ).data,
                        "motivo": item["motivo"],
                        "advertencia": item["advertencia"],
                    }
                    for item in recommendations
                ],
            },
            status=status.HTTP_200_OK,
        )
