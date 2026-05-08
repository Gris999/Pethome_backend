from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema, OpenApiResponse

from apps.AutenticacionySeguridad.mixins.tenant_mixins import TenantViewMixin
from apps.AutenticacionySeguridad.permissions.tenant_rbac import HasComponentPermission

from .serializers import ChatbotCitasRequestSerializer
from .services.intent_detector_service import IntentDetectorService


class ChatbotCitasView(TenantViewMixin, APIView):
    permission_classes = [IsAuthenticated, HasComponentPermission]
    rbac_component = "SERV_CITAS"

    @extend_schema(
        tags=["Bot Citas"],
        request=ChatbotCitasRequestSerializer,
        responses={
            200: OpenApiResponse(description="Respuesta interpretada por la IA."),
            400: OpenApiResponse(description="Datos inválidos."),
        },
    )
    def post(self, request):
        serializer = ChatbotCitasRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        mensaje = serializer.validated_data["mensaje"]

        resultado = IntentDetectorService.detectar_intencion(mensaje)

        return Response(
            {
                "ok": True,
                "mensaje_original": mensaje,
                "resultado": resultado,
            },
            status=status.HTTP_200_OK,
        )