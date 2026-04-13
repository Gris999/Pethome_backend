from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import CategoriaServicio
from ..serializers.categoriaservicio_serializer import CategoriaServicioSerializer


class CategoriaServicioListCreateView(APIView):
    def get(self, request):
        categorias = CategoriaServicio.objects.all()
        serializer = CategoriaServicioSerializer(categorias, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = CategoriaServicioSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CategoriaServicioDetailView(APIView):
    def get_object(self, pk):
        try:
            return CategoriaServicio.objects.get(pk=pk)
        except CategoriaServicio.DoesNotExist:
            return None

    def get(self, request, pk):
        categoria = self.get_object(pk)
        if not categoria:
            return Response(
                {"error": "Categoría no encontrada"},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = CategoriaServicioSerializer(categoria)
        return Response(serializer.data)

    def put(self, request, pk):
        categoria = self.get_object(pk)
        if not categoria:
            return Response(
                {"error": "Categoría no encontrada"},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = CategoriaServicioSerializer(categoria, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        categoria = self.get_object(pk)
        if not categoria:
            return Response(
                {"error": "Categoría no encontrada"},
                status=status.HTTP_404_NOT_FOUND
            )

        categoria.estado = not categoria.estado
        categoria.save()

        return Response({
            "message": "Estado de la categoría actualizado correctamente",
            "estado": categoria.estado
        }, status=status.HTTP_200_OK)