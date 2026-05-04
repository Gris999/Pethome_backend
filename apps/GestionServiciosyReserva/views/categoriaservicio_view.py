from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.AutenticacionySeguridad.events.bitacora_events import (
    BitacoraAccion,
    BitacoraModulo,
    BitacoraResultado,
)
from apps.AutenticacionySeguridad.services.bitacora_register_service import BitacoraService

from ..models import CategoriaServicio
from ..serializers.categoriaservicio_serializer import CategoriaServicioSerializer


def _registrar_bitacora_seguro(func, *args, **kwargs):
    try:
        func(*args, **kwargs)
    except Exception:
        pass


class CategoriaServicioListCreateView(APIView):
    def _vet_id(self, request):
        return getattr(request.user, "veterinaria_id", None)

    def get(self, request):
        categorias = CategoriaServicio.objects.filter(veterinaria_id=self._vet_id(request))
        serializer = CategoriaServicioSerializer(categorias, many=True)

        _registrar_bitacora_seguro(
            BitacoraService.registrar_evento,
            accion=BitacoraAccion.VISUALIZAR,
            descripcion="Listado de categorías de servicio consultado.",
            usuario=request.user,
            request=request,
            modulo=BitacoraModulo.CATALOGOS,
            entidad_tipo="CategoriaServicio",
            resultado=BitacoraResultado.EXITO,
            metadatos={"total": categorias.count()},
        )

        return Response(serializer.data)

    def post(self, request):
        serializer = CategoriaServicioSerializer(data=request.data)
        if serializer.is_valid():
            categoria = serializer.save(veterinaria_id=self._vet_id(request))

            _registrar_bitacora_seguro(
                BitacoraService.registrar_evento,
                accion=BitacoraAccion.CREAR,
                descripcion="Categoría de servicio creada.",
                usuario=request.user,
                request=request,
                modulo=BitacoraModulo.CATALOGOS,
                entidad_tipo="CategoriaServicio",
                entidad_id=getattr(categoria, "id_categoria", ""),
                resultado=BitacoraResultado.EXITO,
                metadatos={"nombre": getattr(categoria, "nombre", "")},
            )

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        _registrar_bitacora_seguro(
            BitacoraService.registrar_evento,
            accion=BitacoraAccion.CREAR,
            descripcion="Falló la creación de categoría de servicio.",
            usuario=request.user,
            request=request,
            modulo=BitacoraModulo.CATALOGOS,
            entidad_tipo="CategoriaServicio",
            resultado=BitacoraResultado.FALLO,
            metadatos={"errores": serializer.errors},
        )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CategoriaServicioDetailView(APIView):
    def _vet_id(self, request):
        return getattr(request.user, "veterinaria_id", None)

    def get_object(self, request, pk):
        try:
            return CategoriaServicio.objects.get(pk=pk, veterinaria_id=self._vet_id(request))
        except CategoriaServicio.DoesNotExist:
            return None

    def get(self, request, pk):
        categoria = self.get_object(request, pk)
        if not categoria:
            _registrar_bitacora_seguro(
                BitacoraService.registrar_evento,
                accion=BitacoraAccion.VISUALIZAR,
                descripcion="Falló la consulta de categoría de servicio: no encontrada.",
                usuario=request.user,
                request=request,
                modulo=BitacoraModulo.CATALOGOS,
                entidad_tipo="CategoriaServicio",
                entidad_id=pk,
                resultado=BitacoraResultado.FALLO,
            )
            return Response(
                {"error": "Categoría no encontrada"},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = CategoriaServicioSerializer(categoria)

        _registrar_bitacora_seguro(
            BitacoraService.registrar_evento,
            accion=BitacoraAccion.VISUALIZAR,
            descripcion="Detalle de categoría de servicio consultado.",
            usuario=request.user,
            request=request,
            modulo=BitacoraModulo.CATALOGOS,
            entidad_tipo="CategoriaServicio",
            entidad_id=getattr(categoria, "id_categoria", pk),
            resultado=BitacoraResultado.EXITO,
        )

        return Response(serializer.data)

    def put(self, request, pk):
        categoria = self.get_object(request, pk)
        if not categoria:
            _registrar_bitacora_seguro(
                BitacoraService.registrar_evento,
                accion=BitacoraAccion.ACTUALIZAR,
                descripcion="Falló la actualización de categoría de servicio: no encontrada.",
                usuario=request.user,
                request=request,
                modulo=BitacoraModulo.CATALOGOS,
                entidad_tipo="CategoriaServicio",
                entidad_id=pk,
                resultado=BitacoraResultado.FALLO,
            )
            return Response(
                {"error": "Categoría no encontrada"},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = CategoriaServicioSerializer(categoria, data=request.data)
        if serializer.is_valid():
            serializer.save(veterinaria_id=self._vet_id(request))

            _registrar_bitacora_seguro(
                BitacoraService.registrar_evento,
                accion=BitacoraAccion.ACTUALIZAR,
                descripcion="Categoría de servicio actualizada.",
                usuario=request.user,
                request=request,
                modulo=BitacoraModulo.CATALOGOS,
                entidad_tipo="CategoriaServicio",
                entidad_id=getattr(categoria, "id_categoria", pk),
                resultado=BitacoraResultado.EXITO,
            )

            return Response(serializer.data)

        _registrar_bitacora_seguro(
            BitacoraService.registrar_evento,
            accion=BitacoraAccion.ACTUALIZAR,
            descripcion="Falló la actualización de categoría de servicio por validación.",
            usuario=request.user,
            request=request,
            modulo=BitacoraModulo.CATALOGOS,
            entidad_tipo="CategoriaServicio",
            entidad_id=getattr(categoria, "id_categoria", pk),
            resultado=BitacoraResultado.FALLO,
            metadatos={"errores": serializer.errors},
        )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        categoria = self.get_object(request, pk)
        if not categoria:
            _registrar_bitacora_seguro(
                BitacoraService.registrar_evento,
                accion=BitacoraAccion.DESACTIVAR,
                descripcion="Falló el cambio de estado de categoría de servicio: no encontrada.",
                usuario=request.user,
                request=request,
                modulo=BitacoraModulo.CATALOGOS,
                entidad_tipo="CategoriaServicio",
                entidad_id=pk,
                resultado=BitacoraResultado.FALLO,
            )
            return Response(
                {"error": "Categoría no encontrada"},
                status=status.HTTP_404_NOT_FOUND
            )

        categoria.estado = not categoria.estado
        categoria.save()

        accion = BitacoraAccion.ACTIVAR if categoria.estado else BitacoraAccion.DESACTIVAR
        _registrar_bitacora_seguro(
            BitacoraService.registrar_evento,
            accion=accion,
            descripcion="Estado de categoría de servicio actualizado.",
            usuario=request.user,
            request=request,
            modulo=BitacoraModulo.CATALOGOS,
            entidad_tipo="CategoriaServicio",
            entidad_id=getattr(categoria, "id_categoria", pk),
            resultado=BitacoraResultado.EXITO,
            metadatos={"estado": categoria.estado},
        )

        return Response({
            "message": "Estado de la categoría actualizado correctamente",
            "estado": categoria.estado
        }, status=status.HTTP_200_OK)
