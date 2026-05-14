from django.db.models import Q
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema

from apps.AutenticacionySeguridad.models import Veterinaria
from apps.AutenticacionySeguridad.mixins.tenant_mixins import TenantViewMixin
from apps.GestionarClinicaVeterinaria.serializers.veterinaria_serializer import (
    VeterinariaSerializer,
)


class VeterinariaListCreateView(TenantViewMixin, generics.ListCreateAPIView):
    serializer_class = VeterinariaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Veterinaria.objects.all()

        search = self.request.query_params.get("search")
        estado = self.request.query_params.get("estado")

        if search:
            queryset = queryset.filter(
                Q(nombre__icontains=search)
                | Q(slug__icontains=search)
                | Q(nit__icontains=search)
                | Q(correo__icontains=search)
                | Q(telefono__icontains=search)
            )

        if estado is not None and estado != "":
            estado_normalizado = estado.lower()

            if estado_normalizado == "true":
                queryset = queryset.filter(estado=True)
            elif estado_normalizado == "false":
                queryset = queryset.filter(estado=False)
        else:
            queryset = queryset.filter(estado=True)

        return queryset.order_by("nombre")

    @extend_schema(tags=["Clinica"], description="Lista veterinarias.")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(tags=["Clinica"], description="Crea una veterinaria.")
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class VeterinariaDetailView(TenantViewMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = VeterinariaSerializer
    permission_classes = [IsAuthenticated]
    queryset = Veterinaria.objects.all()

    @extend_schema(tags=["Clinica"], description="Recupera una veterinaria por id.")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(tags=["Clinica"], description="Actualiza una veterinaria.")
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @extend_schema(tags=["Clinica"], description="Actualiza parcialmente una veterinaria.")
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @extend_schema(
        tags=["Clinica"],
        description="Elimina lógicamente una veterinaria cambiando su estado a false.",
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)

    def perform_destroy(self, instance):
        instance.estado = False
        instance.save(update_fields=["estado"])