from .intent_detector_service import IntentDetectorService
from .chatbot_agendar_service import ChatbotAgendarService
from .chatbot_response_builder import ChatbotResponseBuilder


class ChatbotOrchestratorService:
    @staticmethod
    def procesar_mensaje(*, user, veterinaria_id, mensaje, contexto=None):
        contexto = contexto or {}
        estado = contexto.get("estado")

        if estado == "ESPERANDO_DATOS_AGENDAMIENTO":
            return ChatbotAgendarService.continuar_datos_agendamiento(
                user=user,
                veterinaria_id=veterinaria_id,
                mensaje=mensaje,
                contexto=contexto,
            )

        if estado == "ESPERANDO_SELECCION_SERVICIO":
            return ChatbotAgendarService.continuar_seleccion_servicio(
                user=user,
                veterinaria_id=veterinaria_id,
                mensaje=mensaje,
                contexto=contexto,
            )

        if estado == "ESPERANDO_SELECCION_HORARIO_AGENDAMIENTO":
            return ChatbotAgendarService.continuar_seleccion_horario(
                user=user,
                veterinaria_id=veterinaria_id,
                mensaje=mensaje,
                contexto=contexto,
            )

        if estado == "ESPERANDO_CONFIRMACION_CREAR_CITA":
            return ChatbotAgendarService.continuar_confirmacion_crear_cita(
                user=user,
                veterinaria_id=veterinaria_id,
                mensaje=mensaje,
                contexto=contexto,
            )

        interpretacion = IntentDetectorService.detectar_intencion(mensaje)

        intencion = str(interpretacion.get("intencion", "DESCONOCIDA")).upper()

        if intencion == "AGENDAR_CITA":
            return ChatbotAgendarService.preparar_agendamiento(
                user=user,
                veterinaria_id=veterinaria_id,
                interpretacion=interpretacion,
            )

        if intencion == "LISTAR_SERVICIOS":
            return ChatbotResponseBuilder.success(
                accion="LISTAR_SERVICIOS_PENDIENTE",
                respuesta="Puedo ayudarte a listar los servicios disponibles.",
                data={
                    "interpretacion": interpretacion,
                },
            )

        if intencion == "LISTAR_CITAS":
            return ChatbotResponseBuilder.success(
                accion="LISTAR_CITAS_PENDIENTE",
                respuesta="Puedo ayudarte a consultar tus citas.",
                data={
                    "interpretacion": interpretacion,
                },
            )

        if intencion == "REPROGRAMAR_CITA":
            return ChatbotResponseBuilder.success(
                accion="REPROGRAMAR_CITA_PENDIENTE",
                respuesta="Puedo ayudarte a reprogramar una cita.",
                data={
                    "interpretacion": interpretacion,
                },
            )

        if intencion == "CANCELAR_CITA":
            return ChatbotResponseBuilder.success(
                accion="CANCELAR_CITA_PENDIENTE",
                respuesta="Puedo ayudarte a cancelar una cita.",
                data={
                    "interpretacion": interpretacion,
                },
            )

        return ChatbotResponseBuilder.error(
            code="INTENCION_DESCONOCIDA",
            respuesta="No entendí exactamente qué deseas hacer con tus citas.",
            data={
                "interpretacion": interpretacion,
            },
        )
