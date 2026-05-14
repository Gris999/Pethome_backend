from rest_framework import serializers

from apps.AutenticacionySeguridad.models import Veterinaria


class VeterinariaSerializer(serializers.ModelSerializer):
    id_veterinaria = serializers.IntegerField(read_only=True)

    class Meta:
        model = Veterinaria
        fields = [
            "id_veterinaria",
            "nombre",
            "slug",
            "nit",
            "correo",
            "telefono",
            "direccion",
            "logo",
            "estado",
            "permite_auto_registro_clientes",
            "fecha_creacion",
        ]
        read_only_fields = ["id_veterinaria", "fecha_creacion"]
