from django.urls import path
from apps.AutenticacionySeguridad.views.auth_view import LoginView, LogoutView, MeView
from .views.perfil_views import PerfilView, PerfilDetailView
from .views.register_view import RegisterView   

urlpatterns = [
    path("login/", LoginView.as_view(), name="auth-login"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("me/", MeView.as_view(), name="auth-me"),

    path("perfil/", PerfilView.as_view(), name="perfil"),
    path("perfil/<int:pk>/", PerfilDetailView.as_view(), name="perfil-detail"),
    path("register/", RegisterView.as_view(), name="auth-register"),
]