from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.AutenticacionySeguridad.events.bitacora_events import (
    BitacoraAccion,
    BitacoraModulo,
    BitacoraResultado,
)
from apps.AutenticacionySeguridad.services.bitacora_register_service import BitacoraService

from ..models import Servicio
from ..serializers.servicios_serializer import ServicioSerializer


def _registrar_bitacora_seguro(func, *args, **kwargs):
    try:
        func(*args, **kwargs)
    except Exception:
        pass


class ServicioListCreateView(APIView):
    def get(self, request):
        servicios = Servicio.objects.all()
        serializer = ServicioSerializer(servicios, many=True)

        _registrar_bitacora_seguro(
            BitacoraService.registrar_evento,
            accion=BitacoraAccion.VISUALIZAR,
            descripcion="Listado de servicios consultado.",
            usuario=request.user,
            request=request,
            modulo=BitacoraModulo.SERVICIOS,
            entidad_tipo="Servicio",
            resultado=BitacoraResultado.EXITO,
            metadatos={"total": servicios.count()},
        )

        return Response(serializer.data)

    def post(self, request):
        serializer = ServicioSerializer(data=request.data)
        if serializer.is_valid():
            servicio = serializer.save()

            _registrar_bitacora_seguro(
                BitacoraService.registrar_evento,
                accion=BitacoraAccion.CREAR,
                descripcion="Servicio creado.",
                usuario=request.user,
                request=request,
                modulo=BitacoraModulo.SERVICIOS,
                entidad_tipo="Servicio",
                entidad_id=getattr(servicio, "id_servicio", ""),
                resultado=BitacoraResultado.EXITO,
                metadatos={"nombre": getattr(servicio, "nombre", "")},
            )

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        _registrar_bitacora_seguro(
            BitacoraService.registrar_evento,
            accion=BitacoraAccion.CREAR,
            descripcion="Falló la creación de servicio.",
            usuario=request.user,
            request=request,
            modulo=BitacoraModulo.SERVICIOS,
            entidad_tipo="Servicio",
            resultado=BitacoraResultado.FALLO,
            metadatos={"errores": serializer.errors},
        )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ServicioDetailView(APIView):
    def get_object(self, pk):
        try:
            return Servicio.objects.get(pk=pk)
        except Servicio.DoesNotExist:
            return None

    def get(self, request, pk):
        servicio = self.get_object(pk)
        if not servicio:
            _registrar_bitacora_seguro(
                BitacoraService.registrar_evento,
                accion=BitacoraAccion.VISUALIZAR,
                descripcion="Falló la consulta de servicio: no encontrado.",
                usuario=request.user,
                request=request,
                modulo=BitacoraModulo.SERVICIOS,
                entidad_tipo="Servicio",
                entidad_id=pk,
                resultado=BitacoraResultado.FALLO,
            )
            return Response(
                {"error": "Servicio no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = ServicioSerializer(servicio)

        _registrar_bitacora_seguro(
            BitacoraService.registrar_evento,
            accion=BitacoraAccion.VISUALIZAR,
            descripcion="Detalle de servicio consultado.",
            usuario=request.user,
            request=request,
            modulo=BitacoraModulo.SERVICIOS,
            entidad_tipo="Servicio",
            entidad_id=getattr(servicio, "id_servicio", pk),
            resultado=BitacoraResultado.EXITO,
        )

        return Response(serializer.data)

    def put(self, request, pk):
        servicio = self.get_object(pk)
        if not servicio:
            _registrar_bitacora_seguro(
                BitacoraService.registrar_evento,
                accion=BitacoraAccion.ACTUALIZAR,
                descripcion="Falló la actualización de servicio: no encontrado.",
                usuario=request.user,
                request=request,
                modulo=BitacoraModulo.SERVICIOS,
                entidad_tipo="Servicio",
                entidad_id=pk,
                resultado=BitacoraResultado.FALLO,
            )
            return Response(
                {"error": "Servicio no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = ServicioSerializer(servicio, data=request.data)
        if serializer.is_valid():
            serializer.save()

            _registrar_bitacora_seguro(
                BitacoraService.registrar_evento,
                accion=BitacoraAccion.ACTUALIZAR,
                descripcion="Servicio actualizado.",
                usuario=request.user,
                request=request,
                modulo=BitacoraModulo.SERVICIOS,
                entidad_tipo="Servicio",
                entidad_id=getattr(servicio, "id_servicio", pk),
                resultado=BitacoraResultado.EXITO,
            )

            return Response(serializer.data)

        _registrar_bitacora_seguro(
            BitacoraService.registrar_evento,
            accion=BitacoraAccion.ACTUALIZAR,
            descripcion="Falló la actualización de servicio por validación.",
            usuario=request.user,
            request=request,
            modulo=BitacoraModulo.SERVICIOS,
            entidad_tipo="Servicio",
            entidad_id=getattr(servicio, "id_servicio", pk),
            resultado=BitacoraResultado.FALLO,
            metadatos={"errores": serializer.errors},
        )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        servicio = self.get_object(pk)
        if not servicio:
            _registrar_bitacora_seguro(
                BitacoraService.registrar_evento,
                accion=BitacoraAccion.DESACTIVAR,
                descripcion="Falló el cambio de estado de servicio: no encontrado.",
                usuario=request.user,
                request=request,
                modulo=BitacoraModulo.SERVICIOS,
                entidad_tipo="Servicio",
                entidad_id=pk,
                resultado=BitacoraResultado.FALLO,
            )
            return Response(
                {"error": "Servicio no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )

        servicio.estado = not servicio.estado
        servicio.save()

        accion = BitacoraAccion.ACTIVAR if servicio.estado else BitacoraAccion.DESACTIVAR
        _registrar_bitacora_seguro(
            BitacoraService.registrar_evento,
            accion=accion,
            descripcion="Estado de servicio actualizado.",
            usuario=request.user,
            request=request,
            modulo=BitacoraModulo.SERVICIOS,
            entidad_tipo="Servicio",
            entidad_id=getattr(servicio, "id_servicio", pk),
            resultado=BitacoraResultado.EXITO,
            metadatos={"estado": servicio.estado},
        )

        return Response({
            "message": "Estado actualizado correctamente",
            "estado": servicio.estado
        }, status=status.HTTP_200_OK)