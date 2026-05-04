from django.db import models


class GrupoPermisoComponente(models.Model):
    id_permiso_componente = models.AutoField(primary_key=True)
    puede_ver = models.BooleanField(default=False)
    puede_crear = models.BooleanField(default=False)
    puede_editar = models.BooleanField(default=False)
    puede_eliminar = models.BooleanField(default=False)
    puede_exportar = models.BooleanField(default=False)
    puede_ejecutar = models.BooleanField(default=False)
    estado = models.BooleanField(default=True)
    grupo = models.ForeignKey(
        "AutenticacionySeguridad.GrupoUsuario",
        db_column="id_grupo",
        on_delete=models.CASCADE,
        related_name="permisos_componentes",
    )
    componente = models.ForeignKey(
        "AutenticacionySeguridad.ComponenteSistema",
        db_column="id_componente",
        on_delete=models.CASCADE,
        related_name="permisos_grupo",
    )

    class Meta:
        db_table = "grupo_permiso_componente"
        verbose_name = "Permiso de grupo por componente"
        verbose_name_plural = "Permisos de grupo por componente"
        unique_together = ("grupo", "componente")
