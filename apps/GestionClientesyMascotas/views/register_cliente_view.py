from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from apps.AutenticacionySeguridad.serializers import PerfilCreateSerializer, PerfilSerializer
from apps.AutenticacionySeguridad.models import Rol

class RegisterClienteView(APIView):
    """
    Endpoint público para el auto-registro de usuarios con el rol de "Cliente".
    """
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Crea un nuevo usuario y perfil, forzando el rol a "Cliente".
        """
        data = request.data.copy()

        # 1. Obtener el rol de Cliente. Si no existe, es un error del servidor.
        try:
            rol_cliente = Rol.objects.get(nombre=Rol.RolName.CLIENT)
            data['id_rol'] = rol_cliente.pk
        except Rol.DoesNotExist:
            return Response(
                {"detail": "El rol de cliente no está configurado en el sistema."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # 2. Reutilizar el PerfilCreateSerializer para la creación segura y transaccional.
        # Este serializador ya maneja la validación de correo único y el hasheo de contraseña.
        serializer = PerfilCreateSerializer(data=data)
        
        if serializer.is_valid():
            perfil = serializer.save()
            
            # 3. Devolver una respuesta exitosa con los datos del perfil creado.
            response_data = PerfilSerializer(perfil).data
            return Response(response_data, status=status.HTTP_201_CREATED)

        # Si los datos no son válidos, el serializador devolverá los errores.
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
