from rest_framework import serializers

from apps.GestionClientesyMascotas.models import RegistroEvolucionMascota


class RegistroEvolucionMascotaSerializer(serializers.ModelSerializer):
    mascota_nombre = serializers.CharField(source="mascota.nombre", read_only=True)
    condicion_corporal_display = serializers.CharField(
        source="get_condicion_corporal_display",
        read_only=True,
    )

    class Meta:
        model = RegistroEvolucionMascota
        fields = [
            "id_registro",
            "mascota",
            "mascota_nombre",
            "peso",
            "condicion_corporal",
            "condicion_corporal_display",
            "nota",
            "fecha_registro",
            "fecha_creacion",
        ]
        read_only_fields = [
            "id_registro",
            "mascota",
            "mascota_nombre",
            "condicion_corporal_display",
            "fecha_creacion",
        ]

    def validate_peso(self, value):
        if value <= 0:
            raise serializers.ValidationError("El peso debe ser mayor que 0.")
        return value
