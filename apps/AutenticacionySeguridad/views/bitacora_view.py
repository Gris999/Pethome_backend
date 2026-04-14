from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import PageNumberPagination
from rest_framework import filters, generics

from ..filters import BitacoraFilter
from ..events.bitacora_events import BitacoraAccion, BitacoraModulo, BitacoraResultado
from ..models.bitacora import Bitacora
from ..serializers.bitacora_serializer import BitacoraSerializer
from ..permissions.bitacora_permissions import PuedeVerBitacora
from ..services.bitacora_register_service import BitacoraService


def _registrar_bitacora_seguro(func, *args, **kwargs):
    try:
        func(*args, **kwargs)
    except Exception:
        pass

class BitacoraPagination(PageNumberPagination):
    page_size = 10  
    page_size_query_param = 'page_size' 
    max_page_size = 100

class BitacoraListView(generics.ListAPIView):
    """API de solo lectura para listar eventos de bitácora."""

    queryset = Bitacora.objects.select_related("usuario", "usuario__role").all()
    serializer_class = BitacoraSerializer
    permission_classes = [PuedeVerBitacora]
    pagination_class = BitacoraPagination

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = BitacoraFilter

    search_fields = [
        "descripcion",
        "usuario__correo",
        "usuario__role__nombre",
        "ip",
        "entidad_tipo",
        "entidad_id",
    ]

    ordering_fields = [
        "fecha_hora",
        "accion",
        "resultado",
        "modulo",
    ]
    ordering = ["-fecha_hora"]

    def get(self, request, *args, **kwargs):
        _registrar_bitacora_seguro(
            BitacoraService.registrar_evento,
            accion=BitacoraAccion.VISUALIZAR,
            descripcion="Consulta de listado de bitácora.",
            usuario=request.user,
            request=request,
            modulo=BitacoraModulo.BITACORA,
            entidad_tipo="Bitacora",
            resultado=BitacoraResultado.EXITO,
        )
        return super().get(request, *args, **kwargs)


class BitacoraDetailView(generics.RetrieveAPIView):
    """API de solo lectura para consultar el detalle de un evento."""

    queryset = Bitacora.objects.select_related("usuario", "usuario__role").all()
    serializer_class = BitacoraSerializer
    permission_classes = [PuedeVerBitacora]
    lookup_field = "pk"

    def get(self, request, *args, **kwargs):
        _registrar_bitacora_seguro(
            BitacoraService.registrar_evento,
            accion=BitacoraAccion.VISUALIZAR,
            descripcion="Consulta de detalle de evento de bitácora.",
            usuario=request.user,
            request=request,
            modulo=BitacoraModulo.BITACORA,
            entidad_tipo="Bitacora",
            entidad_id=kwargs.get("pk", ""),
            resultado=BitacoraResultado.EXITO,
        )
        return super().get(request, *args, **kwargs)