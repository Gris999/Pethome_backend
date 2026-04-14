from rest_framework import serializers

from apps.GestionClientesyMascotas.models.vacuna_aplicada import VacunaAplicada


class VacunaAplicadaSerializer(serializers.ModelSerializer):
    class Meta:
        model = VacunaAplicada
        fields = [
            "id_vacuna_aplicada",
            "nombre_vacuna",
            "dosis",
            "fecha_aplicada",
            "fecha_proxima",
            "observacion",
            "estado",
            "fecha_creacion",
        ]
        read_only_fields = [
            "id_vacuna_aplicada",
            "fecha_creacion",
        ]