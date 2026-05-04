from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics
from rest_framework.pagination import PageNumberPagination

from ..filters import BitacoraFilter
from ..models.bitacora import Bitacora
from ..permissions.bitacora_permissions import PuedeVerBitacora
from ..serializers.bitacora_serializer import BitacoraSerializer


class BitacoraPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class BitacoraListView(generics.ListAPIView):
    queryset = Bitacora.objects.all()
    serializer_class = BitacoraSerializer
    permission_classes = [PuedeVerBitacora]
    pagination_class = BitacoraPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = BitacoraFilter
    ordering_fields = ["fecha_hora", "id_bitacora"]
    ordering = ["-fecha_hora"]


class BitacoraDetailView(generics.RetrieveAPIView):
    queryset = Bitacora.objects.all()
    serializer_class = BitacoraSerializer
    permission_classes = [PuedeVerBitacora]
    lookup_field = "pk"
