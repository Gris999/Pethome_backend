from django.db import models
from .user import User  # ajusta si tu import es diferente


class Perfil(models.Model):
    id_perfil = models.AutoField(primary_key=True)

    usuario = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="perfil",
        db_column="id_usuario"
    )

    nombre = models.CharField(max_length=150)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    estado = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "perfil"
        verbose_name = "Perfil"
        verbose_name_plural = "Perfiles"

    def __str__(self):
        return self.nombre