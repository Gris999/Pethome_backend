from rest_framework import serializers

from apps.GestionClientesyMascotas.models import RecordatorioMascota


class RecordatorioMascotaSerializer(serializers.ModelSerializer):
    mascota_nombre = serializers.CharField(source="mascota.nombre", read_only=True)
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)

    class Meta:
        model = RecordatorioMascota
        fields = [
            "id_recordatorio",
            "mascota",
            "mascota_nombre",
            "tipo",
            "tipo_display",
            "titulo",
            "descripcion",
            "fecha_programada",
            "hora_programada",
            "estado",
            "estado_display",
            "notificar",
            "dias_anticipacion",
            "notificacion",
            "fecha_notificacion_enviada",
            "intentos_notificacion",
            "ultimo_error_notificacion",
            "fecha_creacion",
            "fecha_actualizacion",
        ]
        read_only_fields = [
            "id_recordatorio",
            "mascota",
            "mascota_nombre",
            "estado_display",
            "tipo_display",
            "notificacion",
            "fecha_notificacion_enviada",
            "intentos_notificacion",
            "ultimo_error_notificacion",
            "fecha_creacion",
            "fecha_actualizacion",
        ]

    def validate_titulo(self, value):
        text = value.strip()
        if not text:
            raise serializers.ValidationError("El titulo es obligatorio.")
        return text

    def validate_dias_anticipacion(self, value):
        if value < 0:
            raise serializers.ValidationError("Los dias de anticipacion no pueden ser negativos.")
        return value
