from rest_framework import generics, serializers
from rest_framework.permissions import IsAuthenticated
from apps.AutenticacionySeguridad.models.user import User


class UsuarioListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id_usuario", "correo"]


class UsuarioListView(generics.ListAPIView):
    serializer_class = UsuarioListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return User.objects.filter(
            role_id=3,
            is_active=True
        ).order_by("id_usuario")