from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.AutenticacionySeguridad.enums.roles import RoleEnum
from apps.AutenticacionySeguridad.permissions.tenant_rbac import HasComponentPermission
from apps.GestionClientesyMascotas.models import AnalisisImagenMascota, Mascota
from apps.GestionClientesyMascotas.serializers.analisis_imagen_mascota_serializer import (
    AnalisisImagenMascotaCreateSerializer,
    AnalisisImagenMascotaSerializer,
)
from apps.GestionClientesyMascotas.services.analisis_imagen_ia_service import (
    AnalisisImagenIAService,
)


class AnalisisImagenMascotaBaseView(APIView):
    permission_classes = [IsAuthenticated, HasComponentPermission]
    rbac_component = "CLI_MASCOTAS"

    def get_tenant_id(self):
        tenant = getattr(self.request, "tenant", None)
        tenant_id = getattr(tenant, "id", None)
        if tenant_id:
            return tenant_id
        return getattr(self.request.user, "veterinaria_id", None)

    def get_mascota_autorizada(self, id_mascota):
        tenant_id = self.get_tenant_id()
        queryset = Mascota.objects.select_related("usuario", "especie", "raza").filter(
            veterinaria_id=tenant_id,
            estado=True,
        )
        role_name = (
            getattr(getattr(self.request.user, "role", None), "nombre", "") or ""
        ).upper()
        if role_name == RoleEnum.CLIENT.value:
            queryset = queryset.filter(usuario=self.request.user)
        return get_object_or_404(queryset, id_mascota=id_mascota)


class AnalisisImagenMascotaListCreateView(AnalisisImagenMascotaBaseView):
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request, id_mascota):
        mascota = self.get_mascota_autorizada(id_mascota)
        queryset = AnalisisImagenMascota.objects.filter(
            mascota=mascota,
            veterinaria_id=self.get_tenant_id(),
        ).select_related("mascota", "usuario")
        serializer = AnalisisImagenMascotaSerializer(
            queryset,
            many=True,
            context={"request": request},
        )
        return Response({"results": serializer.data, "count": queryset.count()})

    def post(self, request, id_mascota):
        mascota = self.get_mascota_autorizada(id_mascota)
        serializer = AnalisisImagenMascotaCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        analisis = AnalisisImagenMascota.objects.create(
            mascota=mascota,
            usuario=request.user,
            veterinaria=mascota.veterinaria,
            imagen=serializer.validated_data["imagen"],
            estado=AnalisisImagenMascota.Estado.PENDIENTE,
        )

        try:
            result = AnalisisImagenIAService.analizar(analisis)
        except ValidationError as exc:
            detail = exc.detail
            error_message = str(detail)
            if isinstance(detail, dict):
                error_message = str(detail.get("detail") or detail)
            analisis.estado = AnalisisImagenMascota.Estado.ERROR
            analisis.error_mensaje = error_message
            analisis.save(update_fields=["estado", "error_mensaje", "fecha_actualizacion"])
            output = AnalisisImagenMascotaSerializer(
                analisis,
                context={"request": request},
            ).data
            return Response(
                {
                    "detail": "No se pudo analizar la imagen. Intenta con otra imagen o mas tarde.",
                    "analisis": output,
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        analisis.calidad_imagen = result["calidad_imagen"]
        analisis.observaciones_visibles = result["observaciones_visibles"]
        analisis.recomendaciones_generales = result["recomendaciones_generales"]
        analisis.nivel_atencion = result["nivel_atencion"]
        analisis.requiere_consulta = result["requiere_consulta"]
        analisis.mensaje_preventivo = result["mensaje_preventivo"]
        analisis.respuesta_ia_raw = result["respuesta_ia_raw"]
        analisis.estado = AnalisisImagenMascota.Estado.COMPLETADO
        analisis.error_mensaje = ""
        analisis.save()

        output = AnalisisImagenMascotaSerializer(
            analisis,
            context={"request": request},
        ).data
        return Response(output, status=status.HTTP_201_CREATED)


class AnalisisImagenMascotaDetailView(AnalisisImagenMascotaBaseView):
    def get(self, request, id_analisis):
        tenant_id = self.get_tenant_id()
        queryset = AnalisisImagenMascota.objects.select_related(
            "mascota",
            "usuario",
        ).filter(veterinaria_id=tenant_id)

        role_name = (
            getattr(getattr(request.user, "role", None), "nombre", "") or ""
        ).upper()
        if role_name == RoleEnum.CLIENT.value:
            queryset = queryset.filter(mascota__usuario=request.user)

        analisis = get_object_or_404(queryset, id_analisis_imagen=id_analisis)
        serializer = AnalisisImagenMascotaSerializer(
            analisis,
            context={"request": request},
        )
        return Response(serializer.data)
