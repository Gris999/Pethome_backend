from django.db.models import Q
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.AutenticacionySeguridad.models import Perfil, Rol
from apps.AutenticacionySeguridad.events.bitacora_events import (
    BitacoraAccion,
    BitacoraModulo,
    BitacoraResultado,
)
from apps.AutenticacionySeguridad.permissions.permissions import IsAdminRole, IsClientRole
from apps.AutenticacionySeguridad.serializers.perfil_serializer import (
    PerfilSerializer,
    PerfilCreateSerializer,
    PerfilUpdateSerializer,
)
from apps.AutenticacionySeguridad.services.bitacora_register_service import BitacoraService
from apps.AutenticacionySeguridad.services.perfil_service import (
    deactivate_user_profile,
)


def _registrar_bitacora_seguro(func, *args, **kwargs):
    try:
        func(*args, **kwargs)
    except Exception:
        pass


def _obtener_snapshot_perfil(perfil):
    usuario = getattr(perfil, "usuario", None)
    rol = getattr(usuario, "role", None) if usuario else None
    return {
        "correo": getattr(usuario, "correo", None),
        "id_rol": getattr(rol, "id_rol", None),
        "rol": getattr(rol, "nombre", None),
        "estado": getattr(usuario, "is_active", None),
        "nombre": getattr(perfil, "nombre", None),
        "telefono": getattr(perfil, "telefono", None),
        "direccion": getattr(perfil, "direccion", None),
    }


def _construir_metadatos_actualizacion_perfil(snapshot_antes, snapshot_despues, validated_data):
    campos_enviados = sorted(list(validated_data.keys()))
    datos_anteriores = {}
    datos_actualizados = {}
    comparacion = {}

    for campo in campos_enviados:
        if campo == "password":
            datos_anteriores["password"] = "***"
            datos_actualizados["password"] = "***"
            comparacion["password"] = {
                "anterior": "***",
                "actualizado": "***",
            }
            continue

        if campo == "id_rol":
            id_rol_anterior = snapshot_antes.get("id_rol")
            id_rol_actualizado = snapshot_despues.get("id_rol")

            if id_rol_anterior != id_rol_actualizado:
                datos_anteriores["id_rol"] = id_rol_anterior
                datos_actualizados["id_rol"] = id_rol_actualizado
                comparacion["id_rol"] = {
                    "anterior": id_rol_anterior,
                    "actualizado": id_rol_actualizado,
                }

                rol_anterior = snapshot_antes.get("rol")
                rol_actualizado = snapshot_despues.get("rol")
                datos_anteriores["rol"] = rol_anterior
                datos_actualizados["rol"] = rol_actualizado
                comparacion["rol"] = {
                    "anterior": rol_anterior,
                    "actualizado": rol_actualizado,
                }
            continue

        valor_anterior = snapshot_antes.get(campo)
        valor_actualizado = snapshot_despues.get(campo)

        if valor_anterior != valor_actualizado:
            datos_anteriores[campo] = valor_anterior
            datos_actualizados[campo] = valor_actualizado
            comparacion[campo] = {
                "anterior": valor_anterior,
                "actualizado": valor_actualizado,
            }

    return {
        "campos_enviados": campos_enviados,
        "campos_actualizados": sorted(list(comparacion.keys())),
        "datos_anteriores": datos_anteriores,
        "datos_actualizados": datos_actualizados,
        "comparacion": comparacion,
    }


class ClientePagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class ClienteListCreateView(APIView):
    permission_classes = [IsAdminRole]

    def get_queryset(self):
        return (
            Perfil.objects
            .select_related("usuario", "usuario__role")
            .filter(usuario__role__nombre=Rol.RolName.CLIENT)
            .order_by("-id_perfil")
        )

    def get(self, request):
        queryset = self.get_queryset()

        search = request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(
                Q(nombre__icontains=search)
                | Q(usuario__correo__icontains=search)
                | Q(telefono__icontains=search)
                | Q(direccion__icontains=search)
            )

        estado = request.query_params.get("estado")
        if estado is not None:
            estado_norm = estado.lower()
            if estado_norm in {"true", "1", "si", "sí"}:
                queryset = queryset.filter(usuario__is_active=True)
            elif estado_norm in {"false", "0", "no"}:
                queryset = queryset.filter(usuario__is_active=False)

        paginator = ClientePagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = PerfilSerializer(page, many=True)

        _registrar_bitacora_seguro(
            BitacoraService.registrar_evento,
            accion=BitacoraAccion.VISUALIZAR,
            descripcion="Listado de clientes consultado.",
            usuario=request.user,
            request=request,
            modulo=BitacoraModulo.CLIENTES,
            entidad_tipo="Cliente",
            resultado=BitacoraResultado.EXITO,
            metadatos={
                "total": queryset.count(),
                "search": request.query_params.get("search", "").strip(),
                "estado": request.query_params.get("estado"),
            },
        )

        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        data = request.data.copy()

        try:
            rol_cliente = Rol.objects.get(nombre=Rol.RolName.CLIENT)
            data["id_rol"] = rol_cliente.pk
        except Rol.DoesNotExist:
            _registrar_bitacora_seguro(
                BitacoraService.registrar_evento,
                accion=BitacoraAccion.CREAR,
                descripcion="Falló la creación de cliente: rol CLIENT no configurado.",
                usuario=request.user,
                request=request,
                modulo=BitacoraModulo.CLIENTES,
                entidad_tipo="Cliente",
                resultado=BitacoraResultado.FALLO,
            )
            return Response(
                {"detail": "El rol de cliente no está configurado en el sistema."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        serializer = PerfilCreateSerializer(data=data)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError:
            _registrar_bitacora_seguro(
                BitacoraService.registrar_evento,
                accion=BitacoraAccion.CREAR,
                descripcion="Falló la creación de cliente por errores de validación.",
                usuario=request.user,
                request=request,
                modulo=BitacoraModulo.CLIENTES,
                entidad_tipo="Cliente",
                resultado=BitacoraResultado.FALLO,
                metadatos={"errores": serializer.errors},
            )
            raise

        perfil = serializer.save()

        _registrar_bitacora_seguro(
            BitacoraService.registrar_evento,
            accion=BitacoraAccion.CREAR,
            descripcion="Cliente creado desde gestión de clientes.",
            usuario=request.user,
            request=request,
            modulo=BitacoraModulo.CLIENTES,
            entidad_tipo="Cliente",
            entidad_id=getattr(perfil.usuario, "id_usuario", ""),
            resultado=BitacoraResultado.EXITO,
            metadatos={"correo": getattr(perfil.usuario, "correo", "")},
        )

        return Response(PerfilSerializer(perfil).data, status=status.HTTP_201_CREATED)


class ClienteDetailView(APIView):
    permission_classes = [IsAdminRole]

    def get_queryset(self):
        return (
            Perfil.objects
            .select_related("usuario", "usuario__role")
            .filter(usuario__role__nombre=Rol.RolName.CLIENT)
        )

    def get_object(self, pk):
        return get_object_or_404(self.get_queryset(), pk=pk)

    def get(self, request, pk):
        perfil = self.get_object(pk)
        serializer = PerfilSerializer(perfil)

        _registrar_bitacora_seguro(
            BitacoraService.registrar_evento,
            accion=BitacoraAccion.VISUALIZAR,
            descripcion="Detalle de cliente consultado.",
            usuario=request.user,
            request=request,
            modulo=BitacoraModulo.CLIENTES,
            entidad_tipo="Cliente",
            entidad_id=getattr(perfil.usuario, "id_usuario", ""),
            resultado=BitacoraResultado.EXITO,
            metadatos={"correo_objetivo": getattr(perfil.usuario, "correo", "")},
        )

        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        perfil = self.get_object(pk)
        serializer = PerfilUpdateSerializer(perfil, data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError:
            _registrar_bitacora_seguro(
                BitacoraService.registrar_evento,
                accion=BitacoraAccion.ACTUALIZAR,
                descripcion="Falló la actualización completa de cliente.",
                usuario=request.user,
                request=request,
                modulo=BitacoraModulo.CLIENTES,
                entidad_tipo="Cliente",
                entidad_id=getattr(perfil.usuario, "id_usuario", ""),
                resultado=BitacoraResultado.FALLO,
                metadatos={"errores": serializer.errors},
            )
            raise

        snapshot_antes = _obtener_snapshot_perfil(perfil)
        perfil = serializer.save()
        perfil = Perfil.objects.select_related("usuario", "usuario__role").get(pk=perfil.pk)
        snapshot_despues = _obtener_snapshot_perfil(perfil)
        metadatos_cambios = _construir_metadatos_actualizacion_perfil(
            snapshot_antes,
            snapshot_despues,
            serializer.validated_data,
        )

        _registrar_bitacora_seguro(
            BitacoraService.registrar_evento,
            accion=BitacoraAccion.ACTUALIZAR,
            descripcion="Cliente actualizado.",
            usuario=request.user,
            request=request,
            modulo=BitacoraModulo.CLIENTES,
            entidad_tipo="Cliente",
            entidad_id=getattr(perfil.usuario, "id_usuario", ""),
            resultado=BitacoraResultado.EXITO,
            metadatos=metadatos_cambios,
        )

        return Response(PerfilSerializer(perfil).data, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        perfil = self.get_object(pk)
        serializer = PerfilUpdateSerializer(perfil, data=request.data, partial=True)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError:
            _registrar_bitacora_seguro(
                BitacoraService.registrar_evento,
                accion=BitacoraAccion.ACTUALIZAR,
                descripcion="Falló la actualización parcial de cliente.",
                usuario=request.user,
                request=request,
                modulo=BitacoraModulo.CLIENTES,
                entidad_tipo="Cliente",
                entidad_id=getattr(perfil.usuario, "id_usuario", ""),
                resultado=BitacoraResultado.FALLO,
                metadatos={"errores": serializer.errors},
            )
            raise

        snapshot_antes = _obtener_snapshot_perfil(perfil)
        perfil = serializer.save()
        perfil = Perfil.objects.select_related("usuario", "usuario__role").get(pk=perfil.pk)
        snapshot_despues = _obtener_snapshot_perfil(perfil)
        metadatos_cambios = _construir_metadatos_actualizacion_perfil(
            snapshot_antes,
            snapshot_despues,
            serializer.validated_data,
        )

        _registrar_bitacora_seguro(
            BitacoraService.registrar_evento,
            accion=BitacoraAccion.ACTUALIZAR,
            descripcion="Cliente actualizado parcialmente.",
            usuario=request.user,
            request=request,
            modulo=BitacoraModulo.CLIENTES,
            entidad_tipo="Cliente",
            entidad_id=getattr(perfil.usuario, "id_usuario", ""),
            resultado=BitacoraResultado.EXITO,
            metadatos=metadatos_cambios,
        )

        return Response(PerfilSerializer(perfil).data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        perfil = self.get_object(pk)
        deactivate_user_profile(perfil=perfil)

        _registrar_bitacora_seguro(
            BitacoraService.registrar_evento,
            accion=BitacoraAccion.DESACTIVAR,
            descripcion="Cliente desactivado.",
            usuario=request.user,
            request=request,
            modulo=BitacoraModulo.CLIENTES,
            entidad_tipo="Cliente",
            entidad_id=getattr(perfil.usuario, "id_usuario", ""),
            resultado=BitacoraResultado.EXITO,
            metadatos={"correo_objetivo": getattr(perfil.usuario, "correo", "")},
        )

        return Response(status=status.HTTP_204_NO_CONTENT)


class ClienteMeView(APIView):
    permission_classes = [IsClientRole]

    def get_object(self, request):
        return get_object_or_404(
            Perfil.objects.select_related("usuario", "usuario__role"),
            usuario=request.user,
            usuario__role__nombre=Rol.RolName.CLIENT,
        )

    def get(self, request):
        perfil = self.get_object(request)
        serializer = PerfilSerializer(perfil)

        _registrar_bitacora_seguro(
            BitacoraService.registrar_evento,
            accion=BitacoraAccion.VISUALIZAR,
            descripcion="Cliente consultó su propio perfil.",
            usuario=request.user,
            request=request,
            modulo=BitacoraModulo.CLIENTES,
            entidad_tipo="Cliente",
            entidad_id=getattr(perfil.usuario, "id_usuario", ""),
            resultado=BitacoraResultado.EXITO,
        )

        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        perfil = self.get_object(request)
        serializer = PerfilUpdateSerializer(perfil, data=request.data, partial=True)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError:
            _registrar_bitacora_seguro(
                BitacoraService.registrar_evento,
                accion=BitacoraAccion.ACTUALIZAR,
                descripcion="Falló la actualización de perfil propio del cliente.",
                usuario=request.user,
                request=request,
                modulo=BitacoraModulo.CLIENTES,
                entidad_tipo="Cliente",
                entidad_id=getattr(perfil.usuario, "id_usuario", ""),
                resultado=BitacoraResultado.FALLO,
                metadatos={"errores": serializer.errors},
            )
            raise

        snapshot_antes = _obtener_snapshot_perfil(perfil)
        perfil = serializer.save()
        perfil = Perfil.objects.select_related("usuario", "usuario__role").get(pk=perfil.pk)
        snapshot_despues = _obtener_snapshot_perfil(perfil)
        metadatos_cambios = _construir_metadatos_actualizacion_perfil(
            snapshot_antes,
            snapshot_despues,
            serializer.validated_data,
        )

        _registrar_bitacora_seguro(
            BitacoraService.registrar_evento,
            accion=BitacoraAccion.ACTUALIZAR,
            descripcion="Cliente actualizó su propio perfil.",
            usuario=request.user,
            request=request,
            modulo=BitacoraModulo.CLIENTES,
            entidad_tipo="Cliente",
            entidad_id=getattr(perfil.usuario, "id_usuario", ""),
            resultado=BitacoraResultado.EXITO,
            metadatos=metadatos_cambios,
        )

        return Response(PerfilSerializer(perfil).data, status=status.HTTP_200_OK)