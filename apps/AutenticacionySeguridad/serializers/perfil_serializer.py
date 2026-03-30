from rest_framework import serializers
from ..models import Perfil


class PerfilSerializer(serializers.ModelSerializer):
    correo = serializers.EmailField(source="usuario.correo", read_only=True)
    rol = serializers.CharField(source="usuario.role.nombre", read_only=True)

    class Meta:
        model = Perfil
        fields = [
            "id_perfil",
            "usuario",
            "correo",
            "rol",
            "nombre",
            "telefono",
            "direccion",
            "estado",
            "fecha_creacion",
        ]
        read_only_fields = ["id_perfil", "fecha_creacion"]