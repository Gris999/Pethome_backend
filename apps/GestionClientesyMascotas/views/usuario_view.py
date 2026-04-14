from rest_framework import generics, serializers
from rest_framework.permissions import IsAuthenticated
from apps.AutenticacionySeguridad.events.bitacora_events import BitacoraAccion, BitacoraModulo, BitacoraResultado
from apps.AutenticacionySeguridad.services.bitacora_register_service import BitacoraService
from apps.AutenticacionySeguridad.models.user import User


def _registrar_bitacora_seguro(func, *args, **kwargs):
    try:
        func(*args, **kwargs)
    except Exception:
        pass


class UsuarioListSerializer(serializers.ModelSerializer):
    nombre = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id_usuario", "nombre"]

    def get_nombre(self, obj):
        try:
            return obj.perfil.nombre
        except Exception:
            return f"Usuario {obj.id_usuario}"


class UsuarioListView(generics.ListAPIView):
    serializer_class = UsuarioListSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        _registrar_bitacora_seguro(
            BitacoraService.registrar_evento,
            accion=BitacoraAccion.VISUALIZAR,
            descripcion="Consulta de usuarios activos para selector.",
            usuario=request.user,
            request=request,
            modulo=BitacoraModulo.CLIENTES,
            entidad_tipo="User",
            resultado=BitacoraResultado.EXITO,
        )
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return User.objects.filter(
            role_id=3,
            is_active=True
        ).order_by("id_usuario")