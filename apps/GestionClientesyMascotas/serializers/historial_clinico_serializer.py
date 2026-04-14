from rest_framework import serializers

from apps.GestionClientesyMascotas.models.historial_clinico import HistorialClinico
from apps.GestionClientesyMascotas.serializers.tratamiento_serializer import TratamientoSerializer
from apps.GestionClientesyMascotas.serializers.vacuna_aplicada_serializer import VacunaAplicadaSerializer


class HistorialClinicoSerializer(serializers.ModelSerializer):
    tratamientos = TratamientoSerializer(many=True, read_only=True)
    vacunas_aplicadas = VacunaAplicadaSerializer(many=True, read_only=True)

    class Meta:
        model = HistorialClinico
        fields = [
            "id_historial_clinico",
            "fecha_creacion",
            "tratamientos",
            "vacunas_aplicadas",
        ]
        read_only_fields = [
            "id_historial_clinico",
            "fecha_creacion",
        ]