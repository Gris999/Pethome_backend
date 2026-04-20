from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from apps.GestionarClinicaVeterinaria.models import HistorialClinico
from apps.GestionarClinicaVeterinaria.serializers import HistorialClinicoSerializer


class HistorialClinicoPorMascotaView(generics.RetrieveAPIView):
    serializer_class = HistorialClinicoSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        id_mascota = self.kwargs["id_mascota"]
        return get_object_or_404(
            HistorialClinico.objects.select_related(
                "mascota",
                "mascota__especie",
                "mascota__raza",
                "mascota__usuario",
                "mascota__usuario__perfil",
            ).prefetch_related(
                "consultas_clinicas",
                "consultas_clinicas__tratamientos",
                "consultas_clinicas__vacunas_aplicadas",
                "consultas_clinicas__archivos_clinicos",
                "consultas_clinicas__receta",
                "consultas_clinicas__receta__detalles",
            ),
            mascota_id=id_mascota,
            estado=True,
        )