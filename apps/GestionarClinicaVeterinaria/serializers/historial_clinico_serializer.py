from rest_framework import serializers
from apps.GestionarClinicaVeterinaria.models import HistorialClinico
from apps.GestionarClinicaVeterinaria.serializers.consulta_clinica_serializer import ConsultaClinicaSerializer


class HistorialClinicoSerializer(serializers.ModelSerializer):
    mascota_id = serializers.IntegerField(source="mascota.id_mascota", read_only=True)
    mascota_nombre = serializers.CharField(source="mascota.nombre", read_only=True)
    mascota_especie = serializers.CharField(source="mascota.especie.nombre", read_only=True)
    propietario_id = serializers.IntegerField(source="mascota.usuario.id_usuario", read_only=True)
    propietario_nombre = serializers.CharField(source="mascota.usuario.perfil.nombre", read_only=True)
    consultas_clinicas = ConsultaClinicaSerializer(many=True, read_only=True)
    mascota_raza = serializers.SerializerMethodField()

    class Meta:
        model = HistorialClinico
        fields = [
            "id_historial_clinico",
            "mascota",
            "mascota_id",
            "mascota_nombre",
            "mascota_especie",
            "mascota_raza",
            "propietario_id",
            "propietario_nombre",
            "observaciones_generales",
            "fecha_creacion",
            "fecha_actualizacion",
            "estado",
            "consultas_clinicas",
        ]
        read_only_fields = [
            "id_historial_clinico",
            "fecha_creacion",
            "fecha_actualizacion",
        ]

    def get_mascota_raza(self, obj):
        return obj.mascota.raza.nombre if obj.mascota.raza else None