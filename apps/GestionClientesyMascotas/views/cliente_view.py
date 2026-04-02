"""Views de gestión de clientes basadas en usuarios/perfiles."""

from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.AutenticacionySeguridad.models import Perfil, Rol
from apps.AutenticacionySeguridad.permissions import IsAdminRole
from apps.AutenticacionySeguridad.serializers import PerfilCreateSerializer, PerfilSerializer


class ClientePagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class ClienteListCreateView(APIView):
    """CRUD (lista y creación) de clientes usando User + Perfil."""

    permission_classes = [IsAdminRole]

    def get_queryset(self):
        return Perfil.objects.select_related("usuario", "usuario__role").filter(
            usuario__role__nombre=Rol.RolName.CLIENT
        ).order_by("-id_perfil")

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
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        data = request.data.copy()

        try:
            rol_cliente = Rol.objects.get(nombre=Rol.RolName.CLIENT)
            data["id_rol"] = rol_cliente.pk
        except Rol.DoesNotExist:
            return Response(
                {"detail": "El rol de cliente no está configurado en el sistema."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        serializer = PerfilCreateSerializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        perfil = serializer.save()
        return Response(PerfilSerializer(perfil).data, status=status.HTTP_201_CREATED)


class ClienteDetailView(APIView):
    """CRUD (detalle, actualización y eliminación) de clientes."""

    permission_classes = [IsAdminRole]

    def get_object(self, pk: int) -> Perfil:
        queryset = Perfil.objects.select_related("usuario", "usuario__role").filter(
            usuario__role__nombre=Rol.RolName.CLIENT
        )
        return get_object_or_404(queryset, pk=pk)

    def get(self, request, pk):
        perfil = self.get_object(pk)
        serializer = PerfilSerializer(perfil)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        perfil = self.get_object(pk)
        serializer = PerfilSerializer(perfil, data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        perfil = self.get_object(pk)
        serializer = PerfilSerializer(perfil, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @transaction.atomic
    def delete(self, request, pk):
        perfil = self.get_object(pk)
        perfil.usuario.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
