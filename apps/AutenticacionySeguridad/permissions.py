from rest_framework.permissions import BasePermission

from apps.AutenticacionySeguridad.enums.roles import RoleEnum

"""
Permisos personalizados para control de acceso basado en roles.

Este módulo centraliza la lógica de autorización por perfil
para ser reutilizada en las vistas del sistema.
"""

class IsAdminRole(BasePermission):
    message = "Solo los administradores pueden realizar esta acción."

    def has_permission(self, request, view):
        user = request.user
        return (
            user
            and user.is_authenticated
            and user.role
            and user.role.nombre == RoleEnum.ADMIN.value
        )


class IsVeterinarianRole(BasePermission):
    message = "Solo los veterinarios pueden realizar esta acción."

    def has_permission(self, request, view):
        user = request.user
        return (
            user
            and user.is_authenticated
            and user.role
            and user.role.nombre == RoleEnum.VETERINARIAN.value
        )


class IsClientRole(BasePermission):
    message = "Solo los clientes pueden realizar esta acción."

    def has_permission(self, request, view):
        user = request.user
        return (
            user
            and user.is_authenticated
            and user.role
            and user.role.nombre == RoleEnum.CLIENT.value
        )
    
class IsAdminOrVeterinarian(BasePermission):
    message = "Solo administradores o veterinarios pueden realizar esta acción."

    def has_permission(self, request, view):
        user = request.user
        return (
            user
            and user.is_authenticated
            and user.role
            and user.role.nombre in [
                RoleEnum.ADMIN.value,
                RoleEnum.VETERINARIAN.value,
            ]
        )
        
class IsAdminOrClient(BasePermission):
    message = "Solo administradores o clientes pueden realizar esta acción."

    def has_permission(self, request, view):
        user = request.user
        return (
            user
            and user.is_authenticated
            and user.role
            and user.role.nombre in [
                RoleEnum.ADMIN.value,
                RoleEnum.CLIENT.value,
            ]
        )

"""
EQUIPO AVISO IMPORTANTE ESTO PARA CADA APP
El permissions.py define las reglas de acceso a los endpoints.
Si el tiempo lo permite aqui ira los Permisos específicos de la API.

poder crear clases personalizadas de permisos y reglas de acceso por rol o contexto HTTP.
(no tomar atencion por el momento)
"""