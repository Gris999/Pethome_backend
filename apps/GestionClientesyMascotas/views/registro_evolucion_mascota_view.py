from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.AutenticacionySeguridad.enums.roles import RoleEnum
from apps.AutenticacionySeguridad.permissions.tenant_rbac import HasComponentPermission
from apps.GestionClientesyMascotas.models import Mascota, RegistroEvolucionMascota
from apps.GestionClientesyMascotas.serializers.registro_evolucion_mascota_serializer import (
    RegistroEvolucionMascotaSerializer,
)


class RegistroEvolucionAccessMixin:
    permission_classes = [IsAuthenticated, HasComponentPermission]
    rbac_component = "CLI_MASCOTAS"

    def _tenant_id(self):
        tenant = getattr(self.request, "tenant", None)
        return getattr(tenant, "id", None) or getattr(self.request.user, "veterinaria_id", None)

    def _is_client(self):
        role_name = (getattr(getattr(self.request.user, "role", None), "nombre", "") or "").upper()
        return role_name == RoleEnum.CLIENT.value

    def get_mascota(self, id_mascota):
        queryset = Mascota.objects.select_related("usuario", "especie", "raza").filter(
            veterinaria_id=self._tenant_id(),
            estado=True,
        )
        if self._is_client():
            queryset = queryset.filter(usuario=self.request.user)
        return get_object_or_404(queryset, id_mascota=id_mascota)

    def get_registro(self, id_registro):
        queryset = RegistroEvolucionMascota.objects.select_related("mascota", "usuario").filter(
            veterinaria_id=self._tenant_id(),
        )
        if self._is_client():
            queryset = queryset.filter(usuario=self.request.user)
        return get_object_or_404(queryset, id_registro=id_registro)


class RegistroEvolucionListCreateView(RegistroEvolucionAccessMixin, APIView):
    def get(self, request, id_mascota):
        mascota = self.get_mascota(id_mascota)
        registros = mascota.registros_evolucion.select_related("mascota").all()
        serializer = RegistroEvolucionMascotaSerializer(registros, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, id_mascota):
        mascota = self.get_mascota(id_mascota)
        serializer = RegistroEvolucionMascotaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        registro = serializer.save(
            mascota=mascota,
            usuario=mascota.usuario,
            veterinaria=mascota.veterinaria,
        )
        return Response(
            RegistroEvolucionMascotaSerializer(registro).data,
            status=status.HTTP_201_CREATED,
        )


class RegistroEvolucionDetailView(RegistroEvolucionAccessMixin, APIView):
    def get(self, request, id_registro):
        registro = self.get_registro(id_registro)
        return Response(RegistroEvolucionMascotaSerializer(registro).data)

    def patch(self, request, id_registro):
        registro = self.get_registro(id_registro)
        serializer = RegistroEvolucionMascotaSerializer(
            registro,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, id_registro):
        registro = self.get_registro(id_registro)
        registro.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
