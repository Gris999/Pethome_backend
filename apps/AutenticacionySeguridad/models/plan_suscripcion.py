from django.db import models


class PlanSuscripcion(models.Model):
    id_plan = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=120)
    descripcion = models.TextField(blank=True, null=True)
    precio_mensual = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    limite_usuarios = models.IntegerField(default=0)
    limite_mascotas = models.IntegerField(default=0)
    permite_app_movil = models.BooleanField(default=False)
    permite_reportes = models.BooleanField(default=False)
    permite_backup = models.BooleanField(default=False)
    estado = models.BooleanField(default=True)

    class Meta:
        db_table = "plan_suscripcion"
        verbose_name = "Plan de suscripción"
        verbose_name_plural = "Planes de suscripción"

    def __str__(self):
        return self.nombre
