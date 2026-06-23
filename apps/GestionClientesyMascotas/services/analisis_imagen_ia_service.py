import base64
import json
import mimetypes
import re

import requests
from django.conf import settings
from rest_framework.exceptions import ValidationError


class AnalisisImagenIAService:
    API_URL = "https://openrouter.ai/api/v1/chat/completions"

    @classmethod
    def analizar(cls, analisis):
        api_key = getattr(settings, "OPENROUTER_API_KEY", "")
        model = (
            getattr(settings, "OPENROUTER_VISION_MODEL", "")
            or getattr(settings, "OPENROUTER_MODEL", "")
        )

        if not api_key:
            raise ValidationError({"detail": "OPENROUTER_API_KEY no esta configurada."})
        if not model:
            raise ValidationError({"detail": "No hay modelo de OpenRouter configurado."})

        image_url = cls._build_data_url(analisis.imagen)
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Eres un asistente veterinario preventivo. No das diagnosticos "
                        "definitivos ni reemplazas a un veterinario. Analizas solo senales "
                        "visibles en una imagen de mascota y entregas orientacion general."
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": cls._prompt(analisis.mascota.nombre),
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": image_url},
                        },
                    ],
                },
            ],
            "temperature": 0.2,
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": getattr(settings, "OPENROUTER_SITE_URL", "http://localhost:8000"),
            "X-OpenRouter-Title": getattr(settings, "OPENROUTER_SITE_NAME", "PetHome"),
        }

        try:
            response = requests.post(
                cls.API_URL,
                headers=headers,
                data=json.dumps(payload),
                timeout=45,
            )
        except requests.RequestException as exc:
            raise ValidationError({
                "detail": "No se pudo conectar con OpenRouter para analizar la imagen.",
                "error": str(exc),
            })

        if response.status_code >= 400:
            raise ValidationError({
                "detail": "OpenRouter devolvio un error al analizar la imagen.",
                "status_code": response.status_code,
                "response": response.text,
            })

        data = response.json()
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            raise ValidationError({
                "detail": "Respuesta inesperada de OpenRouter.",
                "response": data,
            })

        parsed = cls._parse_json_content(content)
        return cls._normalize_result(parsed, raw_response=data)

    @staticmethod
    def _build_data_url(image_field):
        mime_type = mimetypes.guess_type(image_field.name)[0] or "image/jpeg"
        image_field.open("rb")
        try:
            encoded = base64.b64encode(image_field.read()).decode("utf-8")
        finally:
            image_field.close()
        return f"data:{mime_type};base64,{encoded}"

    @staticmethod
    def _prompt(pet_name):
        return (
            f"Analiza la imagen de la mascota llamada {pet_name}. "
            "Devuelve exclusivamente un JSON valido, sin markdown ni texto extra, con esta forma: "
            "{"
            "\"calidad_imagen\":\"SUFICIENTE|INSUFICIENTE|NO_ANALIZABLE\","
            "\"observaciones_visibles\":[\"texto\"],"
            "\"recomendaciones_generales\":[\"texto\"],"
            "\"nivel_atencion\":\"BAJO|MEDIO|ALTO|URGENTE|NO_ANALIZABLE\","
            "\"requiere_consulta\":true,"
            "\"mensaje_preventivo\":\"texto\""
            "}. "
            "Si la imagen es borrosa, oscura, no muestra una mascota o no permite evaluar senales visibles, "
            "usa calidad_imagen NO_ANALIZABLE o INSUFICIENTE, nivel_atencion NO_ANALIZABLE, "
            "y explica que debe subir una imagen mas clara. "
            "No diagnostiques enfermedades. Incluye siempre que la orientacion no reemplaza una consulta "
            "veterinaria profesional. Si observas senales preocupantes, recomienda agendar consulta."
        )

    @staticmethod
    def _parse_json_content(content):
        text = content.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", text, flags=re.DOTALL)
            if not match:
                raise ValidationError({
                    "detail": "La IA no devolvio un JSON valido.",
                    "response": content,
                })
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                raise ValidationError({
                    "detail": "La IA devolvio una respuesta que no pudo interpretarse.",
                    "response": content,
                })

    @staticmethod
    def _normalize_list(value):
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str) and value.strip():
            return [value.strip()]
        return []

    @classmethod
    def _normalize_result(cls, parsed, raw_response):
        calidad = str(parsed.get("calidad_imagen") or "NO_ANALIZABLE").upper()
        nivel = str(parsed.get("nivel_atencion") or "NO_ANALIZABLE").upper()
        allowed_calidad = {"SUFICIENTE", "INSUFICIENTE", "NO_ANALIZABLE"}
        allowed_nivel = {"BAJO", "MEDIO", "ALTO", "URGENTE", "NO_ANALIZABLE"}

        if calidad not in allowed_calidad:
            calidad = "NO_ANALIZABLE"
        if nivel not in allowed_nivel:
            nivel = "NO_ANALIZABLE"

        mensaje = str(parsed.get("mensaje_preventivo") or "").strip()
        if not mensaje:
            mensaje = (
                "Esta orientacion es preventiva y no reemplaza una consulta "
                "veterinaria profesional."
            )
        elif "no reemplaza" not in mensaje.lower():
            mensaje = (
                f"{mensaje} Esta orientacion no reemplaza una consulta "
                "veterinaria profesional."
            )

        return {
            "calidad_imagen": calidad,
            "observaciones_visibles": cls._normalize_list(
                parsed.get("observaciones_visibles")
            ),
            "recomendaciones_generales": cls._normalize_list(
                parsed.get("recomendaciones_generales")
            ),
            "nivel_atencion": nivel,
            "requiere_consulta": bool(parsed.get("requiere_consulta"))
            or nivel in {"MEDIO", "ALTO", "URGENTE"},
            "mensaje_preventivo": mensaje,
            "respuesta_ia_raw": raw_response,
        }
