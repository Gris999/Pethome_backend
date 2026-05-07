import django_filters

from .models import Pedido, Seguimiento


class SeguimientoFilter(django_filters.FilterSet):
    fecha_desde = django_filters.DateFilter(field_name="fecha_hora", lookup_expr="date__gte")
    fecha_hasta = django_filters.DateFilter(field_name="fecha_hora", lookup_expr="date__lte")
    pedido_id = django_filters.NumberFilter(field_name="pedido_id")
    cita_id = django_filters.NumberFilter(field_name="cita_id")

    class Meta:
        model = Seguimiento
        fields = [
            "tipo_seguimiento",
            "estado_actual",
            "visible_cliente",
            "pedido_id",
            "cita_id",
            "fecha_desde",
            "fecha_hasta",
        ]


class PedidoFilter(django_filters.FilterSet):
    fecha_desde = django_filters.DateFilter(field_name="fecha_pedido", lookup_expr="date__gte")
    fecha_hasta = django_filters.DateFilter(field_name="fecha_pedido", lookup_expr="date__lte")

    class Meta:
        model = Pedido
        fields = ["estado_pedido", "tipo_entrega", "fecha_desde", "fecha_hasta"]
