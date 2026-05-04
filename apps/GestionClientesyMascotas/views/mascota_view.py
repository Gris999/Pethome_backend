from rest_framework import status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.AutenticacionySeguridad.events.bitacora_events import (
    BitacoraAccion,
    BitacoraModulo,
    BitacoraResultado,
)
from apps.AutenticacionySeguridad.services.bitacora_register_service import BitacoraService
from apps.GestionClientesyMascotas.models.mascota import Mascota
from apps.GestionClientesyMascotas.serializers.mascota_serializer import MascotaSerializer


def _registrar_bitacora_seguro(func, *args, **kwargs):
    try:
        func(*args, **kwargs)
    except Exception:
        pass


class MascotaViewSet(viewsets.ModelViewSet):
    serializer_class = MascotaSerializer
    permission_classes = [IsAuthenticated]

    def _vet_id(self):
        return getattr(self.request.user, "veterinaria_id", None)

    def get_queryset(self):
        queryset = Mascota.objects.select_related(
            "usuario",
            "especie",
            "raza"
        ).filter(veterinaria_id=self._vet_id()).order_by("-id_mascota")

        nombre = self.request.query_params.get("nombre")
        especie_id = self.request.query_params.get("especie_id")
        raza_id = self.request.query_params.get("raza_id")
        usuario_id = self.request.query_params.get("usuario_id")
        estado = self.request.query_params.get("estado")

        if nombre:
            queryset = queryset.filter(nombre__icontains=nombre)

        if especie_id:
            queryset = queryset.filter(especie_id=especie_id)

        if raza_id:
            queryset = queryset.filter(raza_id=raza_id)

        if usuario_id:
            queryset = queryset.filter(usuario_id=usuario_id)

        if estado is not None:
            estado_lower = estado.lower()
            if estado_lower in ["true", "1"]:
                queryset = queryset.filter(estado=True)
            elif estado_lower in ["false", "0"]:
                queryset = queryset.filter(estado=False)

        return queryset

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        _registrar_bitacora_seguro(
            BitacoraService.registrar_evento,
            accion=BitacoraAccion.VISUALIZAR,
            descripcion="Listado de mascotas consultado.",
            usuario=request.user,
            request=request,
            modulo=BitacoraModulo.MASCOTAS,
            entidad_tipo="Mascota",
            resultado=BitacoraResultado.EXITO,
            metadatos={
                "nombre": request.query_params.get("nombre"),
                "especie_id": request.query_params.get("especie_id"),
                "raza_id": request.query_params.get("raza_id"),
                "usuario_id": request.query_params.get("usuario_id"),
                "estado": request.query_params.get("estado"),
            },
        )
        return response

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        _registrar_bitacora_seguro(
            BitacoraService.registrar_evento,
            accion=BitacoraAccion.VISUALIZAR,
            descripcion="Detalle de mascota consultado.",
            usuario=request.user,
            request=request,
            modulo=BitacoraModulo.MASCOTAS,
            entidad_tipo="Mascota",
            entidad_id=kwargs.get("pk", ""),
            resultado=BitacoraResultado.EXITO,
        )
        return response

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError:
            _registrar_bitacora_seguro(
                BitacoraService.registrar_evento,
                accion=BitacoraAccion.CREAR,
                descripcion="Falló la creación de mascota por errores de validación.",
                usuario=request.user,
                request=request,
                modulo=BitacoraModulo.MASCOTAS,
                entidad_tipo="Mascota",
                resultado=BitacoraResultado.FALLO,
                metadatos={"errores": serializer.errors},
            )
            raise

        self.perform_create(serializer)
        data = serializer.data

        _registrar_bitacora_seguro(
            BitacoraService.registrar_evento,
            accion=BitacoraAccion.CREAR,
            descripcion="Mascota creada.",
            usuario=request.user,
            request=request,
            modulo=BitacoraModulo.MASCOTAS,
            entidad_tipo="Mascota",
            entidad_id=data.get("id_mascota", ""),
            resultado=BitacoraResultado.EXITO,
            metadatos={
                "nombre": data.get("nombre"),
                "usuario_id": (request.data or {}).get("usuario_id"),
            },
        )

        headers = self.get_success_headers(data)
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        serializer.save(veterinaria_id=self._vet_id())

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError:
            _registrar_bitacora_seguro(
                BitacoraService.registrar_evento,
                accion=BitacoraAccion.ACTUALIZAR,
                descripcion="Falló la actualización de mascota por errores de validación.",
                usuario=request.user,
                request=request,
                modulo=BitacoraModulo.MASCOTAS,
                entidad_tipo="Mascota",
                entidad_id=getattr(instance, "id_mascota", ""),
                resultado=BitacoraResultado.FALLO,
                metadatos={"errores": serializer.errors},
            )
            raise

        self.perform_update(serializer)
        data = serializer.data

        _registrar_bitacora_seguro(
            BitacoraService.registrar_evento,
            accion=BitacoraAccion.ACTUALIZAR,
            descripcion="Mascota actualizada." if not partial else "Mascota actualizada parcialmente.",
            usuario=request.user,
            request=request,
            modulo=BitacoraModulo.MASCOTAS,
            entidad_tipo="Mascota",
            entidad_id=data.get("id_mascota", getattr(instance, "id_mascota", "")),
            resultado=BitacoraResultado.EXITO,
            metadatos={"campos_actualizados": sorted(list(serializer.validated_data.keys()))},
        )

        if getattr(instance, "_prefetched_objects_cache", None):
            instance._prefetched_objects_cache = {}

        return Response(data)

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        mascota_id = getattr(instance, "id_mascota", "")
        nombre = getattr(instance, "nombre", "")
        self.perform_destroy(instance)

        _registrar_bitacora_seguro(
            BitacoraService.registrar_evento,
            accion=BitacoraAccion.ELIMINAR,
            descripcion="Mascota eliminada.",
            usuario=request.user,
            request=request,
            modulo=BitacoraModulo.MASCOTAS,
            entidad_tipo="Mascota",
            entidad_id=mascota_id,
            resultado=BitacoraResultado.EXITO,
            metadatos={"nombre": nombre},
        )

        return Response(status=status.HTTP_204_NO_CONTENT)
