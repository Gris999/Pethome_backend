from django.urls import path

from .views import (
    PedidoDetailView,
    PedidoListView,
    SeguimientoDetailView,
    SeguimientoListView,
)

urlpatterns = [
    path("seguimientos/", SeguimientoListView.as_view(), name="seguimiento-list"),
    path("seguimientos/<int:id_seguimiento>/", SeguimientoDetailView.as_view(), name="seguimiento-detail"),
    path("pedidos/", PedidoListView.as_view(), name="pedido-list"),
    path("pedidos/<int:id_pedido>/", PedidoDetailView.as_view(), name="pedido-detail"),
]
