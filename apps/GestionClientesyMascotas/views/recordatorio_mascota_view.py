from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.AutenticacionySeguridad.enums.roles import RoleEnum
from apps.AutenticacionySeguridad.permissions.tenant_rbac import HasComponentPermission
from apps.GestionClientesyMascotas.models import Mascota, RecordatorioMascota
from apps.GestionClientesyMascotas.serializers.recordatorio_mascota_serializer import (
    RecordatorioMascotaSerializer,
)


class RecordatorioMascotaAccessMixin:
    permission_classes = [IsAuthenticated, HasComponentPermission]
    rbac_component = "CLI_MASCOTAS"

    def _tenant_id(self):
        tenant = getattr(self.request, "tenant", None)
        return getattr(tenant, "id", None) or getattr(self.request.user, "veterinaria_id", None)

    def _is_client(self):
        role_name = (getattr(getattr(self.request.user, "role", None), "nombre", "") or "").upper()
        return role_name == RoleEnum.CLIENT.value

    def get_mascota(self, id_mascota):
        tenant_id = self._tenant_id()
        queryset = Mascota.objects.select_related("usuario", "especie", "raza").filter(
            veterinaria_id=tenant_id,
            estado=True,
        )
        if self._is_client():
            queryset = queryset.filter(usuario=self.request.user)
        return get_object_or_404(queryset, id_mascota=id_mascota)

    def get_recordatorio(self, id_recordatorio):
        tenant_id = self._tenant_id()
        queryset = RecordatorioMascota.objects.select_related("mascota", "usuario").filter(
            veterinaria_id=tenant_id,
        )
        if self._is_client():
            queryset = queryset.filter(usuario=self.request.user)
        return get_object_or_404(queryset, id_recordatorio=id_recordatorio)


class RecordatorioMascotaListCreateView(RecordatorioMascotaAccessMixin, APIView):
    def get(self, request, id_mascota):
        mascota = self.get_mascota(id_mascota)
        queryset = mascota.recordatorios.select_related("mascota").order_by(
            "fecha_programada",
            "hora_programada",
            "-fecha_creacion",
        )
        serializer = RecordatorioMascotaSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, id_mascota):
        mascota = self.get_mascota(id_mascota)
        serializer = RecordatorioMascotaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        recordatorio = serializer.save(
            mascota=mascota,
            usuario=mascota.usuario,
            veterinaria=mascota.veterinaria,
        )
        return Response(
            RecordatorioMascotaSerializer(recordatorio).data,
            status=status.HTTP_201_CREATED,
        )


class RecordatorioMascotaDetailView(RecordatorioMascotaAccessMixin, APIView):
    def get(self, request, id_recordatorio):
        recordatorio = self.get_recordatorio(id_recordatorio)
        return Response(RecordatorioMascotaSerializer(recordatorio).data)

    def patch(self, request, id_recordatorio):
        recordatorio = self.get_recordatorio(id_recordatorio)
        serializer = RecordatorioMascotaSerializer(
            recordatorio,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class RecordatorioMascotaCompletarView(RecordatorioMascotaAccessMixin, APIView):
    def post(self, request, id_recordatorio):
        recordatorio = self.get_recordatorio(id_recordatorio)
        recordatorio.estado = RecordatorioMascota.EstadoRecordatorio.COMPLETADO
        recordatorio.save(update_fields=["estado", "fecha_actualizacion"])
        return Response(RecordatorioMascotaSerializer(recordatorio).data)


class RecordatorioMascotaCancelarView(RecordatorioMascotaAccessMixin, APIView):
    def post(self, request, id_recordatorio):
        recordatorio = self.get_recordatorio(id_recordatorio)
        recordatorio.estado = RecordatorioMascota.EstadoRecordatorio.CANCELADO
        recordatorio.save(update_fields=["estado", "fecha_actualizacion"])
        return Response(RecordatorioMascotaSerializer(recordatorio).data)
