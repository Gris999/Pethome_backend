from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from apps.GestionarClinicaVeterinaria.models import ConsultaClinica, ArchivoClinico
from apps.GestionarClinicaVeterinaria.serializers import ArchivoClinicoSerializer


class ArchivoClinicoListCreateView(generics.ListCreateAPIView):
    serializer_class = ArchivoClinicoSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        id_consulta = self.kwargs["id_consulta_clinica"]
        return (
            ArchivoClinico.objects.filter(
                consulta_clinica_id=id_consulta,
                estado=True,
            )
            .select_related("consulta_clinica")
            .order_by("-fecha_subida", "-id_archivo_clinico")
        )

    def perform_create(self, serializer):
        id_consulta = self.kwargs["id_consulta_clinica"]
        consulta = get_object_or_404(
            ConsultaClinica,
            pk=id_consulta,
            estado=True,
        )

        archivo = self.request.FILES.get("archivo")
        nombre_archivo = self.request.data.get("nombre_archivo")
        extension = None
        tamano_bytes = None
        tipo_archivo = self.request.data.get("tipo_archivo", "OTRO")

        if archivo:
            extension = archivo.name.split(".")[-1].lower() if "." in archivo.name else ""
            tamano_bytes = archivo.size

            if not nombre_archivo:
                nombre_archivo = archivo.name

            if tipo_archivo == "OTRO":
                if extension in ["jpg", "jpeg", "png", "webp"]:
                    tipo_archivo = "IMAGEN"
                elif extension == "pdf":
                    tipo_archivo = "PDF"
                elif extension in ["doc", "docx"]:
                    tipo_archivo = "WORD"

        serializer.save(
            consulta_clinica=consulta,
            nombre_archivo=nombre_archivo or "archivo_clinico",
            extension=extension,
            tamano_bytes=tamano_bytes,
            tipo_archivo=tipo_archivo,
        )


class ArchivoClinicoDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ArchivoClinicoSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    lookup_url_kwarg = "id_archivo_clinico"

    def get_queryset(self):
        return ArchivoClinico.objects.filter(
            estado=True
        ).select_related("consulta_clinica")

    def perform_destroy(self, instance):
        instance.estado = False
        instance.save(update_fields=["estado"])