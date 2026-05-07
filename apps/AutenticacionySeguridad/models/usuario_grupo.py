from django.db import models


class UsuarioGrupo(models.Model):
    id_usuario_grupo = models.AutoField(primary_key=True)
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    estado = models.BooleanField(default=True)
    usuario = models.ForeignKey(
        "AutenticacionySeguridad.User",
        db_column="id_usuario",
        on_delete=models.CASCADE,
        related_name="grupos_asignados",
    )
    grupo = models.ForeignKey(
        "AutenticacionySeguridad.GrupoUsuario",
        db_column="id_grupo",
        on_delete=models.CASCADE,
        related_name="usuarios_asignados",
    )

    class Meta:
        db_table = "usuario_grupo"
        verbose_name = "Usuario grupo"
        verbose_name_plural = "Usuarios grupo"
        unique_together = ("usuario", "grupo")
