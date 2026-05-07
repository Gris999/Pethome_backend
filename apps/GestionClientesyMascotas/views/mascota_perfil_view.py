from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, OpenApiTypes, extend_schema, inline_serializer
from rest_framework import serializers

from apps.AutenticacionySeguridad.enums.roles import RoleEnum
from apps.AutenticacionySeguridad.events.bitacora_events import BitacoraAccion, BitacoraModulo, BitacoraResultado
from apps.AutenticacionySeguridad.permissions.tenant_rbac import HasComponentPermission
from apps.AutenticacionySeguridad.services.bitacora_register_service import BitacoraService
from apps.GestionClientesyMascotas.models.mascota import Mascota
from apps.GestionClientesyMascotas.serializers.mascota_serializer import MascotaSerializer
from apps.GestionarClinicaVeterinaria.models import HistorialClinico
from apps.GestionarClinicaVeterinaria.serializers.historial_clinico_serializer import HistorialClinicoSerializer
from apps.GestionServiciosyReserva.models.citas import Cita


def _registrar_bitacora_seguro(*, accion, descripcion, usuario, request, modulo, entidad_tipo, entidad_id="", resultado=BitacoraResultado.EXITO, metadatos=None):
    try:
        BitacoraService.registrar_evento(
            accion=accion,
            descripcion=descripcion,
            usuario=usuario,
            request=request,
            modulo=modulo,
            entidad_tipo=entidad_tipo,
            entidad_id=entidad_id,
            resultado=resultado,
            metadatos=metadatos or {},
        )
    except Exception:
        # En desarrollo no debe romper la funcionalidad si bitácora falla.
        pass


class MascotaPerfilView(APIView):
    permission_classes = [IsAuthenticated, HasComponentPermission]
    rbac_component = "CLI_MASCOTAS"

    @extend_schema(
        tags=["Mascotas"],
        responses={200: MascotaSerializer, 404: OpenApiResponse(description="No encontrado.")},
    )
    def get(self, request, id_mascota):
        queryset = Mascota.objects.select_related(
            "usuario",
            "usuario__perfil",
            "especie",
            "raza",
        )

        tenant = getattr(request, "tenant", None)
        tenant_id = getattr(tenant, "id", None)

        user = request.user
        rol = user.role.nombre.upper()

        if rol == RoleEnum.CLIENT.value:
            mascota = get_object_or_404(
                queryset,
                id_mascota=id_mascota,
                usuario=user,
                veterinaria_id=tenant_id,
            )
        else:
            mascota = get_object_or_404(
                queryset,
                id_mascota=id_mascota,
                veterinaria_id=tenant_id,
            )

        mascota_data = MascotaSerializer(mascota, context={"request": request}).data
        # Dirección principal: perfil del dueño
        direccion_principal = ""
        if hasattr(mascota.usuario, "perfil") and mascota.usuario.perfil:
            direccion_principal = mascota.usuario.perfil.direccion or ""

        # Direcciones derivadas de citas (sin tabla nueva): únicas y no vacías
        direcciones_citas = list(
            Cita.objects.filter(
                mascota=mascota,
                veterinaria_id=tenant_id,
                direccion_cita__isnull=False,
            )
            .exclude(direccion_cita__exact="")
            .order_by("-fecha_programada", "-hora_inicio")
            .values_list("direccion_cita", flat=True)
            .distinct()
        )

        historial_qs = Cita.objects.filter(mascota=mascota, veterinaria_id=tenant_id)
        historial_total = historial_qs.count()
        historial_finalizado = historial_qs.filter(estado=Cita.EstadoChoices.COMPLETADA).count()
        historial_seguimiento = historial_qs.exclude(estado=Cita.EstadoChoices.COMPLETADA).count()

        payload = {
            "mascota": mascota_data,
            "direcciones": {
                "principal": direccion_principal,
                "historial": direcciones_citas,
                "total": (1 if direccion_principal else 0) + len(direcciones_citas),
            },
            "historial": {
                "total": historial_total,
                "finalizado": historial_finalizado,
                "seguimiento": historial_seguimiento,
            },
        }

        _registrar_bitacora_seguro(
            accion=BitacoraAccion.PERFIL_MASCOTA_CONSULTADO,
            descripcion="Consulta al perfil consolidado de mascota (CU9).",
            usuario=request.user,
            request=request,
            modulo=BitacoraModulo.MASCOTAS,
            entidad_tipo="Mascota",
            entidad_id=mascota.id_mascota,
            resultado=BitacoraResultado.EXITO,
            metadatos={"id_veterinaria": tenant_id},
        )

        return Response(payload, status=status.HTTP_200_OK)


class MascotaHistorialClinicoView(APIView):
    permission_classes = [IsAuthenticated, HasComponentPermission]
    rbac_component = "CLI_MASCOTAS"

    @extend_schema(
        tags=["Mascotas"],
        responses={
            200: inline_serializer(
                name="MascotaHistorialResponse",
                fields={"historial_clinico": HistorialClinicoSerializer()},
            ),
            404: OpenApiResponse(description="No existe historial clínico."),
        },
    )
    def get(self, request, id_mascota):
        queryset = Mascota.objects.select_related(
            "usuario",
            "usuario__perfil",
            "especie",
            "raza",
        )

        tenant = getattr(request, "tenant", None)
        tenant_id = getattr(tenant, "id", None)

        user = request.user
        rol = user.role.nombre.upper()

        if rol == RoleEnum.CLIENT.value:
            mascota = get_object_or_404(
                queryset,
                id_mascota=id_mascota,
                usuario=user,
                veterinaria_id=tenant_id,
            )
        else:
            mascota = get_object_or_404(
                queryset,
                id_mascota=id_mascota,
                veterinaria_id=tenant_id,
            )

        historial = HistorialClinico.objects.filter(
            mascota=mascota,
            estado=True
        ).select_related(
            "mascota",
            "mascota__usuario",
            "mascota__usuario__perfil",
            "mascota__especie",
            "mascota__raza",
        ).prefetch_related(
            "consultas_clinicas",
            "consultas_clinicas__tratamientos",
            "consultas_clinicas__vacunas_aplicadas",
            "consultas_clinicas__archivos_clinicos",
            "consultas_clinicas__receta",
            "consultas_clinicas__receta__detalles",
        ).first()

        if not historial:
            return Response(
                {"detail": "No existe historial clínico para esta mascota."},
                status=status.HTTP_404_NOT_FOUND,
            )

        historial_data = HistorialClinicoSerializer(
            historial,
            context={"request": request}
        ).data

        return Response(
            {"historial_clinico": historial_data},
            status=status.HTTP_200_OK
        )


class MascotaHistorialServiciosView(APIView):
    permission_classes = [IsAuthenticated, HasComponentPermission]
    rbac_component = "CLI_HISTORIALES"

    @extend_schema(
        tags=["Mascotas"],
        parameters=[
            OpenApiParameter("estado", OpenApiTypes.STR, required=False, description="Filtro opcional de estado."),
        ],
        responses={
            200: inline_serializer(
                name="MascotaHistorialServiciosResponse",
                fields={
                    "items": serializers.ListField(child=serializers.DictField()),
                    "total": serializers.IntegerField(),
                },
            ),
            404: OpenApiResponse(description="Mascota no encontrada."),
        },
    )
    def get(self, request, id_mascota):
        queryset = Mascota.objects.select_related("usuario", "especie", "raza")
        tenant = getattr(request, "tenant", None)
        tenant_id = getattr(tenant, "id", None)
        user = request.user
        rol = user.role.nombre.upper()

        if rol == RoleEnum.CLIENT.value:
            mascota = get_object_or_404(
                queryset,
                id_mascota=id_mascota,
                usuario=user,
                veterinaria_id=tenant_id,
            )
        else:
            mascota = get_object_or_404(
                queryset,
                id_mascota=id_mascota,
                veterinaria_id=tenant_id,
            )

        citas = Cita.objects.select_related("servicio").filter(
            mascota=mascota,
            veterinaria_id=tenant_id,
        )
        estado = request.query_params.get("estado")
        if estado:
            citas = citas.filter(estado=estado)

        citas = citas.order_by("-fecha_programada", "-hora_inicio")
        items = [
            {
                "id_cita": c.id_cita,
                "fecha": c.fecha_programada,
                "tipo_servicio": c.servicio.nombre if c.servicio else "",
                "observaciones": c.descripcion or "",
                "estado": c.estado,
                "modalidad": c.modalidad,
                "direccion_cita": c.direccion_cita or "",
            }
            for c in citas
        ]

        _registrar_bitacora_seguro(
            accion=BitacoraAccion.HISTORIAL_SERVICIOS_CONSULTADO,
            descripcion="Consulta al historial de servicios por mascota (CU9).",
            usuario=request.user,
            request=request,
            modulo=BitacoraModulo.MASCOTAS,
            entidad_tipo="Mascota",
            entidad_id=mascota.id_mascota,
            resultado=BitacoraResultado.EXITO,
            metadatos={"id_veterinaria": tenant_id, "total_items": len(items)},
        )

        return Response({"items": items, "total": len(items)}, status=status.HTTP_200_OK)


class MascotasMeView(APIView):
    permission_classes = [IsAuthenticated, HasComponentPermission]
    rbac_component = "CLI_MASCOTAS"

    @extend_schema(
        tags=["Mascotas"],
        responses={
            200: inline_serializer(
                name="MascotasMeResponse",
                fields={"mascotas": MascotaSerializer(many=True)},
            )
        },
    )
    def get(self, request):
        tenant = getattr(request, "tenant", None)
        tenant_id = getattr(tenant, "id", None)
        mascotas = Mascota.objects.select_related(
            "usuario",
            "usuario__perfil",
            "especie",
            "raza",
        ).filter(
            usuario=request.user,
            veterinaria_id=tenant_id,
        ).order_by("-fecha_registro")

        mascotas_data = MascotaSerializer(
            mascotas,
            many=True,
            context={"request": request}
        ).data

        return Response(
            {"mascotas": mascotas_data},
            status=status.HTTP_200_OK
        )
