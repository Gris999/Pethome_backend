from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.AutenticacionySeguridad.permissions.permissions import IsClientRole
from apps.GestionClientesyMascotas.models.mascota import Mascota
from apps.GestionClientesyMascotas.serializers.mascota_serializer import MascotaSerializer
from apps.GestionClientesyMascotas.serializers.historial_clinico_serializer import HistorialClinicoSerializer
from apps.GestionClientesyMascotas.serializers.tratamiento_serializer import TratamientoSerializer
from apps.GestionClientesyMascotas.serializers.vacuna_aplicada_serializer import VacunaAplicadaSerializer


class MascotaPerfilView(APIView):
    """Obtiene el perfil básico de una mascota."""
    permission_classes = [IsAuthenticated, IsClientRole]

    def get(self, request, id_mascota):
        """
        Retorna solo los datos básicos de la mascota.
        """
        mascota = get_object_or_404(
            Mascota.objects.select_related(
                "usuario",
                "especie",
                "raza",
            ),
            id_mascota=id_mascota,
            usuario=request.user,
        )

        mascota_data = MascotaSerializer(mascota, context={"request": request}).data
        return Response(mascota_data, status=status.HTTP_200_OK)


class MascotaHistorialClinicoView(APIView):
    """Obtiene el historial clínico + tratamientos de una mascota."""
    permission_classes = [IsAuthenticated, IsClientRole]

    def get(self, request, id_mascota):
        """
        Retorna historial clínico con seus tratamientos asociados.
        """
        mascota = get_object_or_404(
            Mascota.objects.prefetch_related(
                "historiales_clinicos__tratamientos",
            ),
            id_mascota=id_mascota,
            usuario=request.user,
        )

        historial = mascota.historiales_clinicos.first()
        
        if not historial:
            return Response(
                {"detail": "No existe historial clínico para esta mascota."},
                status=status.HTTP_404_NOT_FOUND
            )

        historial_data = HistorialClinicoSerializer(
            historial,
            context={"request": request}
        ).data
        
        tratamientos = historial.tratamientos.all()
        tratamientos_data = TratamientoSerializer(
            tratamientos,
            many=True,
            context={"request": request}
        ).data

        response_data = {
            "historial_clinico": historial_data,
            "tratamientos": tratamientos_data,
        }

        return Response(response_data, status=status.HTTP_200_OK)


class MascotaVacunasView(APIView):
    """Obtiene las vacunas aplicadas de una mascota."""
    permission_classes = [IsAuthenticated, IsClientRole]

    def get(self, request, id_mascota):
        """
        Retorna lista de vacunas aplicadas a la mascota.
        """
        mascota = get_object_or_404(
            Mascota.objects.prefetch_related(
                "historiales_clinicos__vacunas_aplicadas",
            ),
            id_mascota=id_mascota,
            usuario=request.user,
        )

        historial = mascota.historiales_clinicos.first()
        
        if not historial:
            return Response(
                {"vacunas_aplicadas": []},
                status=status.HTTP_200_OK
            )

        vacunas = historial.vacunas_aplicadas.all()
        vacunas_data = VacunaAplicadaSerializer(
            vacunas,
            many=True,
            context={"request": request}
        ).data

        return Response(
            {"vacunas_aplicadas": vacunas_data},
            status=status.HTTP_200_OK
        )


class MascotasMeView(APIView):
    """Obtiene todas las mascotas del usuario autenticado."""
    permission_classes = [IsAuthenticated, IsClientRole]

    def get(self, request):
        """
        Retorna lista de todas las mascotas del usuario.
        """
        mascotas = Mascota.objects.select_related(
            "usuario",
            "especie",
            "raza",
        ).filter(
            usuario=request.user
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