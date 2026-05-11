from django.db.models import Prefetch, Q

from ..models import Pedido, Seguimiento
from ..permissions import (
    get_user_role_name,
    is_client_role,
    is_privileged_role,
)


class PedidoSelector:
    @staticmethod
    def base_queryset():
        return Pedido.objects.select_related(
            "usuario",
            "usuario__role",
            "usuario__perfil",
            "veterinaria",
        ).prefetch_related(
            "detalles__producto",
            Prefetch(
                "seguimientos",
                queryset=Seguimiento.objects.select_related("usuario", "cita").order_by("-fecha_hora"),
            ),
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
            return queryset.filter(usuario_id=user.id_usuario)

        if is_privileged_role(role_name):
            return queryset

        # Rol no identificado: fallback seguro a datos propios.
        return queryset.filter(Q(usuario_id=user.id_usuario))

    @classmethod
    def get_pedidos_for_user(cls, user):
        queryset = cls.base_queryset().order_by("-fecha_pedido")
        return cls.scope_queryset_for_user(queryset, user)

    @classmethod
    def get_pedido_detail_for_user(cls, user, pedido_id):
        queryset = cls.base_queryset()
        scoped = cls.scope_queryset_for_user(queryset, user)
        return scoped.filter(id_pedido=pedido_id).first()
