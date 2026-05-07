from django.db.models import Q

from ..models import Seguimiento
from ..permissions import (
    get_user_role_name,
    is_client_role,
    is_privileged_role,
    is_veterinarian_role,
)


class SeguimientoSelector:
    @staticmethod
    def base_queryset():
        return Seguimiento.objects.select_related(
            "usuario",
            "usuario__role",
            "usuario__perfil",
            "veterinaria",
            "cita",
            "cita__servicio",
            "pedido",
        )

    @staticmethod
    def scope_queryset_for_user(queryset, user):
        if getattr(user, "is_superuser", False):
            return queryset

        tenant_id = getattr(user, "veterinaria_id", None)
        if not tenant_id:
            return queryset.none()

        queryset = queryset.filter(veterinaria_id=tenant_id)

        role_name = get_user_role_name(user)
        if is_client_role(role_name):
            return queryset.filter(
                visible_cliente=True,
            ).filter(
                Q(usuario_id=user.id_usuario)
                | Q(cita__usuario_id=user.id_usuario)
                | Q(pedido__usuario_id=user.id_usuario)
            )

        if is_veterinarian_role(role_name):
            # Si existe consulta clinica asociada a la cita, se filtra por veterinario asignado.
            # Cuando no existe esa asociacion, se mantiene al menos aislamiento por veterinaria.
            return queryset.filter(
                Q(cita__consultas_clinicas__isnull=True)
                | Q(cita__consultas_clinicas__usuario_veterinario_id=user.id_usuario)
                | Q(pedido__isnull=False)
            ).distinct()

        if is_privileged_role(role_name):
            return queryset

        # Rol no identificado: fallback seguro a datos propios.
        return queryset.filter(
            Q(usuario_id=user.id_usuario)
            | Q(cita__usuario_id=user.id_usuario)
            | Q(pedido__usuario_id=user.id_usuario)
        )

    @classmethod
    def get_seguimientos_for_user(cls, user):
        queryset = cls.base_queryset().order_by("-fecha_hora")
        return cls.scope_queryset_for_user(queryset, user)

    @classmethod
    def get_seguimiento_detail_for_user(cls, user, seguimiento_id):
        queryset = cls.base_queryset()
        scoped = cls.scope_queryset_for_user(queryset, user)
        return scoped.filter(id_seguimiento=seguimiento_id).first()
