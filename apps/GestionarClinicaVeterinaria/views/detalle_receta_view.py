from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from apps.GestionarClinicaVeterinaria.models import DetalleReceta, Receta
from apps.GestionarClinicaVeterinaria.serializers import DetalleRecetaSerializer


class DetalleRecetaListCreateView(generics.ListCreateAPIView):
    serializer_class = DetalleRecetaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        id_receta = self.kwargs["id_receta"]
        vet_id = getattr(self.request.user, "veterinaria_id", None)
        return DetalleReceta.objects.filter(
            receta_id=id_receta,
            receta__consulta_clinica__veterinaria_id=vet_id,
        ).select_related("receta", "producto").order_by("id_detalle_receta")

    def perform_create(self, serializer):
        id_receta = self.kwargs["id_receta"]
        vet_id = getattr(self.request.user, "veterinaria_id", None)
        receta = get_object_or_404(
            Receta,
            pk=id_receta,
            consulta_clinica__veterinaria_id=vet_id,
            estado=True,
        )
        serializer.save(receta=receta)


class DetalleRecetaDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = DetalleRecetaSerializer
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = "id_detalle_receta"

    def get_queryset(self):
        vet_id = getattr(self.request.user, "veterinaria_id", None)
        return DetalleReceta.objects.filter(
            receta__consulta_clinica__veterinaria_id=vet_id
        ).select_related("receta", "producto")

    def perform_destroy(self, instance):
        instance.delete()
