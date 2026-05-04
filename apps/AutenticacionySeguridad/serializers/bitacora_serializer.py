import base64

from rest_framework import serializers

from ..models.bitacora import Bitacora


class BitacoraSerializer(serializers.ModelSerializer):
    id_veterinaria = serializers.IntegerField(source="veterinaria_id", read_only=True)
    payload_b64 = serializers.SerializerMethodField()

    class Meta:
        model = Bitacora
        fields = [
            "id_bitacora",
            "id_veterinaria",
            "fecha_hora",
            "payload_b64",
        ]
        read_only_fields = fields

    def get_payload_b64(self, obj):
        if not obj.payload:
            return ""
        return base64.b64encode(bytes(obj.payload)).decode("ascii")
