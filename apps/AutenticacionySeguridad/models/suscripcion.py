from django.db import models


class Suscripcion(models.Model):
    ESTADOS = [
        ("ACTIVA", "Activa"),
        ("VENCIDA", "Vencida"),
        ("SUSPENDIDA", "Suspendida"),
        ("CANCELADA", "Cancelada"),
        ("PRUEBA", "Prueba"),
    ]

    id_suscripcion = models.AutoField(primary_key=True)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(blank=True, null=True)
    estado_suscripcion = models.CharField(max_length=20, choices=ESTADOS, default="PRUEBA")
    renovacion_automatica = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    metodo_pago = models.CharField(max_length=50, blank=True, null=True)
    fecha_pago = models.DateTimeField(blank=True, null=True)
    veterinaria = models.ForeignKey(
        "AutenticacionySeguridad.Veterinaria",
        db_column="id_veterinaria",
        on_delete=models.CASCADE,
        related_name="suscripciones",
    )
    plan = models.ForeignKey(
        "AutenticacionySeguridad.PlanSuscripcion",
        db_column="id_plan",
        on_delete=models.PROTECT,
        related_name="suscripciones",
    )

    class Meta:
        db_table = "suscripcion"
        verbose_name = "Suscripción"
        verbose_name_plural = "Suscripciones"

    def __str__(self):
        return f"{self.veterinaria_id} - {self.estado_suscripcion}"
