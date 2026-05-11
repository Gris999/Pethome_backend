from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..filters import PedidoFilter
from ..permissions import HasVeterinariaOrSuperuser
from ..selectors import PedidoSelector
from ..serializers import PedidoDetailSerializer, PedidoListSerializer


class PedidoListView(APIView):
    permission_classes = [IsAuthenticated, HasVeterinariaOrSuperuser]

    def get(self, request):
        queryset = PedidoSelector.get_pedidos_for_user(request.user)
        filterset = PedidoFilter(request.GET, queryset=queryset)

        if not filterset.is_valid():
            return Response(
                {"detail": "Parametros de filtro invalidos.", "errors": filterset.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = PedidoListSerializer(filterset.qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PedidoDetailView(APIView):
    permission_classes = [IsAuthenticated, HasVeterinariaOrSuperuser]

    def get(self, request, id_pedido):
        pedido = PedidoSelector.get_pedido_detail_for_user(request.user, id_pedido)
        if pedido is None:
            return Response(
                {"detail": "Pedido no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = PedidoDetailSerializer(pedido)
        return Response(serializer.data, status=status.HTTP_200_OK)
