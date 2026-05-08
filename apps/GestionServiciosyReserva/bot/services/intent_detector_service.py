# apps/GestionServiciosyReserva/bot/services/intent_detector_service.py

import json
import re

from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .openrouter_service import OpenRouterService


class IntentDetectorService:
    @staticmethod
    def _limpiar_json_respuesta(texto):
        """
        Limpia respuestas tipo ```json ... ``` por si el modelo las devuelve.
        """
        if not texto:
            return texto

        texto = texto.strip()

        if texto.startswith("```"):
            texto = re.sub(r"^```json\s*", "", texto, flags=re.IGNORECASE)
            texto = re.sub(r"^```\s*", "", texto)
            texto = re.sub(r"\s*```$", "", texto)

        return texto.strip()

    @staticmethod
    def detectar_intencion(mensaje_usuario):
        fecha_actual = timezone.localdate().isoformat()

        system_prompt = f"""
Eres un asistente de una plataforma web veterinaria llamada PetHome.

Tu tarea es interpretar mensajes de usuarios sobre citas veterinarias.

Fecha actual del sistema: {fecha_actual}

Debes devolver SOLO JSON válido, sin markdown, sin explicaciones.

Intenciones permitidas:
- AGENDAR_CITA
- REPROGRAMAR_CITA
- CANCELAR_CITA
- LISTAR_CITAS
- LISTAR_SERVICIOS
- CONSULTAR_AGENDA
- DESCONOCIDA

Formato obligatorio:
{{
  "intencion": "AGENDAR_CITA",
  "datos": {{
    "mascota_nombre": null,
    "servicio_nombre": null,
    "fecha_texto": null,
    "fecha_programada": null,
    "hora_inicio": null,
    "modalidad": null,
    "motivo_cancelacion": null
  }},
  "faltan": [],
  "respuesta": "Texto breve para responder al usuario"
}}

Reglas obligatorias:
- No inventes IDs.
- No inventes horarios disponibles.
- No confirmes que una cita fue creada.
- No confirmes que una cita fue registrada.
- No confirmes que una cita fue cancelada.
- No confirmes que una cita fue reprogramada.
- Nunca uses frases como "he registrado", "cita registrada", "cita agendada", "cita confirmada" o similares.
- Solo interpreta la intención y los datos mencionados por el usuario.
- Si el usuario dice "mañana", calcula la fecha usando la fecha actual del sistema.
- Si puedes calcular una fecha exacta, coloca esa fecha en "fecha_programada" con formato YYYY-MM-DD.
- Usa "fecha_texto" para guardar el texto original o interpretado de la fecha.
- Si el usuario no menciona fecha exacta o relativa clara, deja "fecha_programada" en null.
- Si el usuario no menciona hora exacta, deja "hora_inicio" en null.
- La hora debe estar en formato HH:MM.
- modalidad solo puede ser CLINICA, DOMICILIO o null.
- Si faltan datos importantes, colócalos en "faltan".
- Para AGENDAR_CITA normalmente se necesitan: mascota_nombre, servicio_nombre, fecha_programada, hora_inicio y modalidad.
- Si el mensaje no tiene relación con citas veterinarias, usa DESCONOCIDA.
- La respuesta debe ser breve y debe indicar que se verificará la información antes de confirmar cualquier acción.
"""

        messages = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": mensaje_usuario,
            },
        ]

        raw_response = OpenRouterService.chat(messages)
        clean_response = IntentDetectorService._limpiar_json_respuesta(raw_response)

        try:
            data = json.loads(clean_response)
        except json.JSONDecodeError:
            raise ValidationError({
                "detail": "La IA no devolvió JSON válido.",
                "raw_response": raw_response,
            })

        return data