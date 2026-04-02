"""URLs para Cliente."""

from django.urls import path
from .views.cliente_view import ClienteDetailView, ClienteListCreateView
from .views.register_cliente_view import RegisterClienteView

app_name = 'clientes'

urlpatterns = [
    # Registro público de clientes.
    path('register/', RegisterClienteView.as_view(), name='cliente-register'),

    # CRUD administrativo de clientes basado en usuarios/perfiles.
    path('', ClienteListCreateView.as_view(), name='cliente-list-create'),
    path('<int:pk>/', ClienteDetailView.as_view(), name='cliente-detail'),
]
