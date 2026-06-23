from django.contrib import admin

from apps.GestionClientesyMascotas.models import AnalisisImagenMascota


@admin.register(AnalisisImagenMascota)
class AnalisisImagenMascotaAdmin(admin.ModelAdmin):
    list_display = (
        "id_analisis_imagen",
        "mascota",
        "usuario",
        "nivel_atencion",
        "requiere_consulta",
        "estado",
        "fecha_creacion",
    )
    list_filter = ("estado", "nivel_atencion", "requiere_consulta", "fecha_creacion")
    search_fields = ("mascota__nombre", "usuario__correo", "mensaje_preventivo")
    readonly_fields = ("fecha_creacion", "fecha_actualizacion")
