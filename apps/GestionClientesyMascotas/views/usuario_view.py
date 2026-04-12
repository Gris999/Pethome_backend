from rest_framework import generics, serializers
from rest_framework.permissions import IsAuthenticated
from apps.AutenticacionySeguridad.models.user import User


class UsuarioListSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "nombre_completo"]

    def get_nombre_completo(self, obj):
        first_name = getattr(obj, "first_name", "") or ""
        last_name = getattr(obj, "last_name", "") or ""
        return f"{first_name} {last_name}".strip()


class UsuarioListView(generics.ListAPIView):
    serializer_class = UsuarioListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return User.objects.all().order_by("first_name", "last_name", "username")