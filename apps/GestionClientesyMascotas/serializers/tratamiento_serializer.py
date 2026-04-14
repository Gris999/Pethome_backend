from rest_framework import serializers

from apps.GestionClientesyMascotas.models.tratamiento import Tratamiento


class TratamientoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tratamiento
        fields = [
            "id_tratamiento",
            "tipo",
            "descripcion",
            "fecha_ini",
            "fecha_fin",
            "observacion",
            "estado",
            "fecha_creacion",
            "fecha_actualizacion",
        ]
        read_only_fields = [
            "id_tratamiento",
            "fecha_creacion",
            "fecha_actualizacion",
        ]