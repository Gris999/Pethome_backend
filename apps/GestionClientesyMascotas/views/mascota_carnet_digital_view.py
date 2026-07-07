from django.shortcuts import get_object_or_404
from django.core import signing
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.AutenticacionySeguridad.enums.roles import RoleEnum
from apps.AutenticacionySeguridad.permissions.tenant_rbac import HasComponentPermission
from apps.GestionClientesyMascotas.models import Mascota
from apps.GestionClientesyMascotas.services.carnet_digital_mascota_service import (
    CarnetDigitalMascotaService,
)


class MascotaCarnetDigitalView(APIView):
    permission_classes = [IsAuthenticated, HasComponentPermission]
    rbac_component = "CLI_MASCOTAS"

    def get(self, request, id_mascota):
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

        mascota = get_object_or_404(queryset, id_mascota=id_mascota)
        payload = CarnetDigitalMascotaService.build_payload(
            mascota=mascota,
            request=request,
        )
        return Response(payload, status=status.HTTP_200_OK)


class MascotaCarnetPublicoView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, token):
        try:
            payload = CarnetDigitalMascotaService.build_public_payload(token=token)
        except signing.BadSignature:
            return Response(
                {"detail": "Carnet invalido o alterado."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Mascota.DoesNotExist:
            return Response(
                {"detail": "Carnet no disponible."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(payload, status=status.HTTP_200_OK)
