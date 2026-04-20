from rest_framework import serializers
from apps.GestionarClinicaVeterinaria.models import ArchivoClinico


class ArchivoClinicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArchivoClinico
        fields = [
            "id_archivo_clinico",
            "consulta_clinica",
            "nombre_archivo",
            "archivo",
            "tipo_archivo",
            "extension",
            "tamano_bytes",
            "descripcion",
            "fecha_subida",
            "estado",
        ]
        read_only_fields = ["id_archivo_clinico", "fecha_subida"]