from rest_framework import serializers
from ..models import User
from ..serializers.rol_serializer import RolSerializer


class UserSerializer(serializers.ModelSerializer):
    rol = RolSerializer(source="role", read_only=True)
    id_veterinaria = serializers.IntegerField(source="veterinaria_id", read_only=True)

    class Meta:
        model = User
        fields = [
            "id_usuario",
            "correo",
            "id_veterinaria",
            "rol",
            "is_active",
            "date_joined",
        ]
