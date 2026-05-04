from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.AutenticacionySeguridad.events.bitacora_events import (
    BitacoraAccion,
    BitacoraModulo,
    BitacoraResultado,
)
from apps.AutenticacionySeguridad.services.bitacora_register_service import BitacoraService

from ..models import PrecioServicio
from ..serializers.precioservicio_serializer import PrecioServicioSerializer


def _registrar_bitacora_seguro(func, *args, **kwargs):
    try:
        func(*args, **kwargs)
    except Exception:
        pass


class PrecioServicioListCreateView(APIView):
    def _vet_id(self, request):
        return getattr(request.user, "veterinaria_id", None)

    def get(self, request):
        precios = PrecioServicio.objects.filter(veterinaria_id=self._vet_id(request))
        serializer = PrecioServicioSerializer(precios, many=True)

        _registrar_bitacora_seguro(
            BitacoraService.registrar_evento,
            accion=BitacoraAccion.VISUALIZAR,
            descripcion="Listado de precios de servicio consultado.",
            usuario=request.user,
            request=request,
            modulo=BitacoraModulo.PRECIOS,
            entidad_tipo="PrecioServicio",
            resultado=BitacoraResultado.EXITO,
            metadatos={"total": precios.count()},
        )

        return Response(serializer.data)

    def post(self, request):
        serializer = PrecioServicioSerializer(data=request.data)
        if serializer.is_valid():
            precio = serializer.save(veterinaria_id=self._vet_id(request))

            _registrar_bitacora_seguro(
                BitacoraService.registrar_evento,
                accion=BitacoraAccion.CREAR,
                descripcion="Precio de servicio creado.",
                usuario=request.user,
                request=request,
                modulo=BitacoraModulo.PRECIOS,
                entidad_tipo="PrecioServicio",
                entidad_id=getattr(precio, "id_precio", ""),
                resultado=BitacoraResultado.EXITO,
                metadatos={"servicio_id": getattr(precio, "servicio_id", None)},
            )

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        _registrar_bitacora_seguro(
            BitacoraService.registrar_evento,
            accion=BitacoraAccion.CREAR,
            descripcion="Falló la creación de precio de servicio.",
            usuario=request.user,
            request=request,
            modulo=BitacoraModulo.PRECIOS,
            entidad_tipo="PrecioServicio",
            resultado=BitacoraResultado.FALLO,
            metadatos={"errores": serializer.errors},
        )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PrecioServicioDetailView(APIView):
    def _vet_id(self, request):
        return getattr(request.user, "veterinaria_id", None)

    def get_object(self, request, pk):
        try:
            return PrecioServicio.objects.get(pk=pk, veterinaria_id=self._vet_id(request))
        except PrecioServicio.DoesNotExist:
            return None

    def get(self, request, pk):
        precio = self.get_object(request, pk)
        if not precio:
            _registrar_bitacora_seguro(
                BitacoraService.registrar_evento,
                accion=BitacoraAccion.VISUALIZAR,
                descripcion="Falló la consulta de precio: no encontrado.",
                usuario=request.user,
                request=request,
                modulo=BitacoraModulo.PRECIOS,
                entidad_tipo="PrecioServicio",
                entidad_id=pk,
                resultado=BitacoraResultado.FALLO,
            )
            return Response(
                {"error": "Precio no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = PrecioServicioSerializer(precio)

        _registrar_bitacora_seguro(
            BitacoraService.registrar_evento,
            accion=BitacoraAccion.VISUALIZAR,
            descripcion="Detalle de precio de servicio consultado.",
            usuario=request.user,
            request=request,
            modulo=BitacoraModulo.PRECIOS,
            entidad_tipo="PrecioServicio",
            entidad_id=getattr(precio, "id_precio", pk),
            resultado=BitacoraResultado.EXITO,
        )

        return Response(serializer.data)

    def put(self, request, pk):
        precio = self.get_object(request, pk)
        if not precio:
            _registrar_bitacora_seguro(
                BitacoraService.registrar_evento,
                accion=BitacoraAccion.ACTUALIZAR,
                descripcion="Falló la actualización de precio: no encontrado.",
                usuario=request.user,
                request=request,
                modulo=BitacoraModulo.PRECIOS,
                entidad_tipo="PrecioServicio",
                entidad_id=pk,
                resultado=BitacoraResultado.FALLO,
            )
            return Response(
                {"error": "Precio no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = PrecioServicioSerializer(precio, data=request.data)
        if serializer.is_valid():
            serializer.save(veterinaria_id=self._vet_id(request))

            _registrar_bitacora_seguro(
                BitacoraService.registrar_evento,
                accion=BitacoraAccion.ACTUALIZAR,
                descripcion="Precio de servicio actualizado.",
                usuario=request.user,
                request=request,
                modulo=BitacoraModulo.PRECIOS,
                entidad_tipo="PrecioServicio",
                entidad_id=getattr(precio, "id_precio", pk),
                resultado=BitacoraResultado.EXITO,
            )

            return Response(serializer.data)

        _registrar_bitacora_seguro(
            BitacoraService.registrar_evento,
            accion=BitacoraAccion.ACTUALIZAR,
            descripcion="Falló la actualización de precio por validación.",
            usuario=request.user,
            request=request,
            modulo=BitacoraModulo.PRECIOS,
            entidad_tipo="PrecioServicio",
            entidad_id=getattr(precio, "id_precio", pk),
            resultado=BitacoraResultado.FALLO,
            metadatos={"errores": serializer.errors},
        )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        precio = self.get_object(request, pk)
        if not precio:
            _registrar_bitacora_seguro(
                BitacoraService.registrar_evento,
                accion=BitacoraAccion.DESACTIVAR,
                descripcion="Falló el cambio de estado de precio: no encontrado.",
                usuario=request.user,
                request=request,
                modulo=BitacoraModulo.PRECIOS,
                entidad_tipo="PrecioServicio",
                entidad_id=pk,
                resultado=BitacoraResultado.FALLO,
            )
            return Response(
                {"error": "Precio no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )

        precio.estado = not precio.estado
        precio.save()

        accion = BitacoraAccion.ACTIVAR if precio.estado else BitacoraAccion.DESACTIVAR
        _registrar_bitacora_seguro(
            BitacoraService.registrar_evento,
            accion=accion,
            descripcion="Estado del precio de servicio actualizado.",
            usuario=request.user,
            request=request,
            modulo=BitacoraModulo.PRECIOS,
            entidad_tipo="PrecioServicio",
            entidad_id=getattr(precio, "id_precio", pk),
            resultado=BitacoraResultado.EXITO,
            metadatos={"estado": precio.estado},
        )

        return Response({
            "message": "Estado del precio actualizado correctamente",
            "estado": precio.estado
        }, status=status.HTTP_200_OK)
