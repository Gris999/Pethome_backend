from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from apps.AutenticacionySeguridad.models import User, Perfil, Rol
from apps.AutenticacionySeguridad.serializers.user_serializer import UserSerializer
from django.contrib.auth.hashers import make_password


from rest_framework.permissions import AllowAny

class RegisterView(APIView):
    permission_classes = [AllowAny]  

    def post(self, request):
        try:
            data = request.data

            #  Validar correo único
            if User.objects.filter(correo=data.get("correo")).exists():
                return Response(
                    {"detail": "El correo ya está registrado."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Obtener o crear rol CLIENTE automáticamente
            rol_cliente, _ = Rol.objects.get_or_create(
                nombre=Rol.RolName.CLIENT,
                defaults={"descripcion": "Cliente del sistema"}
            )

            #  Crear usuario
            user = User.objects.create(
                correo=data.get("correo"),
                password=make_password(data.get("password")),
                role=rol_cliente,
            )

            #  Crear perfil
            perfil = Perfil.objects.create(
                usuario=user,
                nombre=data.get("nombre"),
                telefono=data.get("telefono"),
                direccion=data.get("direccion"),
                estado=True,
            )

            return Response(
                {
                    "user": UserSerializer(user).data,
                    "perfil": {
                        "nombre": perfil.nombre,
                        "telefono": perfil.telefono,
                        "direccion": perfil.direccion,
                    },
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        