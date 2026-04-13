from rest_framework import permissions
from ..enums.roles import RoleEnum
from ..models.bitacora import Bitacora
from ..events.bitacora_events import BitacoraModulo
from ..services.bitacora_register_service import BitacoraService


def _registrar_acceso_denegado_seguro(request, mensaje):
    try:
        usuario = request.user if getattr(request.user, "is_authenticated", False) else None
        BitacoraService.registrar_acceso_denegado(
            request=request,
            descripcion=mensaje,
            usuario=usuario,
            modulo=BitacoraModulo.BITACORA,
            metadatos={
                "metodo": getattr(request, "method", ""),
                "path": getattr(request, "path", ""),
            },
        )
    except Exception:
        pass

class PuedeVerBitacora(permissions.BasePermission):
    message = "No tienes permisos para consultar la bitácora."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            _registrar_acceso_denegado_seguro(request, self.message)
            return False

        if user.is_superuser:
            return True

        role = getattr(user, "role", None)
        if role and role.nombre == RoleEnum.ADMIN.value:
            return True

        permiso_lectura = f"{Bitacora._meta.app_label}.view_{Bitacora._meta.model_name}"
        permitido = bool(
            user.has_perm(permiso_lectura)
        )

        if not permitido:
            _registrar_acceso_denegado_seguro(request, self.message)

        return permitido