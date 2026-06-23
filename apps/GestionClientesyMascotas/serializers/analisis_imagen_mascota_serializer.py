from pathlib import Path

from PIL import Image, UnidentifiedImageError
from rest_framework import serializers

from apps.GestionClientesyMascotas.models import AnalisisImagenMascota


class AnalisisImagenMascotaSerializer(serializers.ModelSerializer):
    mascota_nombre = serializers.CharField(source="mascota.nombre", read_only=True)
    imagen_url = serializers.SerializerMethodField()

    class Meta:
        model = AnalisisImagenMascota
        fields = [
            "id_analisis_imagen",
            "mascota",
            "mascota_nombre",
            "imagen_url",
            "calidad_imagen",
            "observaciones_visibles",
            "recomendaciones_generales",
            "nivel_atencion",
            "requiere_consulta",
            "mensaje_preventivo",
            "estado",
            "error_mensaje",
            "fecha_creacion",
            "fecha_actualizacion",
        ]
        read_only_fields = fields

    def get_imagen_url(self, obj):
        if not obj.imagen:
            return ""
        url = obj.imagen.url
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(url)
        return url


class AnalisisImagenMascotaCreateSerializer(serializers.Serializer):
    imagen = serializers.ImageField(required=False)
    file = serializers.ImageField(required=False)

    allowed_ext = {".jpg", ".jpeg", ".png", ".webp"}
    allowed_content_types = {"image/jpeg", "image/png", "image/webp"}
    max_size_bytes = 5 * 1024 * 1024

    def validate(self, attrs):
        image = attrs.get("imagen") or attrs.get("file")
        if not image:
            raise serializers.ValidationError({
                "imagen": "Debe enviar una imagen en el campo 'imagen' o 'file'."
            })

        ext = Path(image.name).suffix.lower()
        if ext not in self.allowed_ext:
            raise serializers.ValidationError({
                "imagen": "Formato no permitido. Use JPG, PNG o WEBP."
            })

        content_type = getattr(image, "content_type", "")
        if content_type and content_type not in self.allowed_content_types:
            raise serializers.ValidationError({
                "imagen": "El archivo enviado no tiene un tipo de imagen valido."
            })

        if image.size > self.max_size_bytes:
            raise serializers.ValidationError({
                "imagen": "La imagen supera el tamano maximo permitido (5MB)."
            })

        current_position = image.tell()
        try:
            image.seek(0)
            with Image.open(image) as img:
                img.verify()
        except (UnidentifiedImageError, OSError):
            raise serializers.ValidationError({
                "imagen": "El archivo enviado no es una imagen valida."
            })
        finally:
            image.seek(current_position)

        attrs["imagen"] = image
        return attrs
