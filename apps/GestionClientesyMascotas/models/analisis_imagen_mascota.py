from django.conf import settings
from django.db import models


def analisis_imagen_upload_to(instance, filename):
    tenant_id = getattr(instance, "veterinaria_id", None) or "sin_vet"
    mascota_id = getattr(instance, "mascota_id", None) or "sin_mascota"
    return f"vet_{tenant_id}/mascotas/{mascota_id}/analisis_ia/{filename}"


class AnalisisImagenMascota(models.Model):
    class CalidadImagen(models.TextChoices):
        SUFICIENTE = "SUFICIENTE", "Suficiente"
        INSUFICIENTE = "INSUFICIENTE", "Insuficiente"
        NO_ANALIZABLE = "NO_ANALIZABLE", "No analizable"

    class NivelAtencion(models.TextChoices):
        BAJO = "BAJO", "Bajo"
        MEDIO = "MEDIO", "Medio"
        ALTO = "ALTO", "Alto"
        URGENTE = "URGENTE", "Urgente"
        NO_ANALIZABLE = "NO_ANALIZABLE", "No analizable"

    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        COMPLETADO = "COMPLETADO", "Completado"
        ERROR = "ERROR", "Error"

    id_analisis_imagen = models.AutoField(primary_key=True)
    mascota = models.ForeignKey(
        "GestionClientesyMascotas.Mascota",
        db_column="id_mascota",
        on_delete=models.CASCADE,
        related_name="analisis_imagenes",
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        db_column="id_usuario",
        on_delete=models.PROTECT,
        related_name="analisis_imagenes_mascota",
    )
    veterinaria = models.ForeignKey(
        "AutenticacionySeguridad.Veterinaria",
        db_column="id_veterinaria",
        on_delete=models.PROTECT,
        related_name="analisis_imagenes_mascota",
    )
    imagen = models.ImageField(upload_to=analisis_imagen_upload_to)
    calidad_imagen = models.CharField(
        max_length=20,
        choices=CalidadImagen.choices,
        default=CalidadImagen.NO_ANALIZABLE,
    )
    observaciones_visibles = models.JSONField(default=list, blank=True)
    recomendaciones_generales = models.JSONField(default=list, blank=True)
    nivel_atencion = models.CharField(
        max_length=20,
        choices=NivelAtencion.choices,
        default=NivelAtencion.NO_ANALIZABLE,
    )
    requiere_consulta = models.BooleanField(default=False)
    mensaje_preventivo = models.TextField(blank=True)
    respuesta_ia_raw = models.JSONField(null=True, blank=True)
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.PENDIENTE,
    )
    error_mensaje = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "analisis_imagen_mascota"
        verbose_name = "Analisis de imagen de mascota"
        verbose_name_plural = "Analisis de imagenes de mascotas"
        ordering = ["-fecha_creacion"]

    def __str__(self):
        return f"Analisis IA #{self.id_analisis_imagen} - {self.mascota.nombre}"
