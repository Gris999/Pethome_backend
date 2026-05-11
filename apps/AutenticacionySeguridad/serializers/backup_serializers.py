from rest_framework import serializers
from ..models.backup_restore import BackupRestore
from ..models.backup_config import BackupConfig
from ..models.user import User


class UserBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id_usuario", "correo"]


class BackupRestoreSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.CharField(source="usuario.perfil.nombre", read_only=True)
    usuario_correo = serializers.CharField(source="usuario.correo", read_only=True)
    veterinaria_nombre = serializers.CharField(source="veterinaria.nombre", read_only=True)
    
    class Meta:
        model = BackupRestore
        fields = [
            "id_backup_restore",
            "tipo",
            "fecha_hora",
            "ruta_archivo",
            "proveedor_almacenamiento",
            "estado",
            "hash_archivo",
            "motivo",
            "usuario",
            "usuario_nombre",
            "usuario_correo",
            "veterinaria",
            "veterinaria_nombre",
        ]
        read_only_fields = [
            "id_backup_restore",
            "fecha_hora",
            "hash_archivo",
            "usuario_nombre",
            "usuario_correo",
            "veterinaria_nombre",
        ]


class BackupConfigSerializer(serializers.ModelSerializer):
    veterinaria_nombre = serializers.CharField(source="veterinaria.nombre", read_only=True)
    
    class Meta:
        model = BackupConfig
        fields = [
            "id_backup_config",
            "veterinaria",
            "veterinaria_nombre",
            "frecuencia",
            "dias_retención",
            "último_backup",
            "próximo_backup_programado",
            "activo",
            "creado",
            "actualizado",
        ]
        read_only_fields = [
            "id_backup_config",
            "veterinaria_nombre",
            "creado",
            "actualizado",
            "próximo_backup_programado",
        ]

    def validate_frecuencia(self, value):
        valid_choices = [choice[0] for choice in BackupConfig.FRECUENCIAS]
        if value not in valid_choices:
            raise serializers.ValidationError(
                f"Frecuencia debe ser una de: {', '.join(valid_choices)}"
            )
        return value

    def validate_dias_retención(self, value):
        if value < 1 or value > 365:
            raise serializers.ValidationError("Días de retención debe estar entre 1 y 365")
        return value
