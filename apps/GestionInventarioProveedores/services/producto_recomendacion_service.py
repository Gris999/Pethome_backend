from decimal import Decimal

from django.db.models import Case, DecimalField, IntegerField, Q, Sum, Value, When
from django.db.models.functions import Coalesce
from django.utils import timezone

from apps.GestionInventarioProveedores.models import Producto, PuntoInventario


class ProductoRecomendacionService:
    SPECIES_TO_PRODUCT_TYPE = {
        "CANINO": Producto.TipoMascota.PERRO,
        "PERRO": Producto.TipoMascota.PERRO,
        "FELINO": Producto.TipoMascota.GATO,
        "GATO": Producto.TipoMascota.GATO,
        "AVE": Producto.TipoMascota.AVE,
        "ROEDOR": Producto.TipoMascota.ROEDOR,
        "PEZ": Producto.TipoMascota.PEZ,
    }

    CATEGORY_KEYWORDS = (
        "alimento",
        "higiene",
        "juguete",
        "accesorio",
        "cuidado",
    )

    @classmethod
    def get_for_pet(cls, *, mascota, tenant_id, request=None, limit=12):
        product_type = cls._product_type_for_pet(mascota)
        base_queryset = Producto.objects.select_related(
            "categoria_producto",
            "proveedor",
            "veterinaria",
        ).filter(
            veterinaria_id=tenant_id,
            estado=True,
            visible_catalogo=True,
        ).annotate(
            stock_disponible_catalogo=Coalesce(
                Sum(
                    "stocks_por_punto__cantidad",
                    filter=(
                        Q(stocks_por_punto__punto_inventario__estado=True)
                        & Q(
                            stocks_por_punto__punto_inventario__tipo=(
                                PuntoInventario.TipoPunto.ALMACEN_GENERAL
                            )
                        )
                        & Q(stocks_por_punto__cantidad__gt=0)
                        & (
                            Q(stocks_por_punto__fecha_vencimiento_lote__isnull=True)
                            | Q(
                                stocks_por_punto__fecha_vencimiento_lote__gt=(
                                    timezone.localdate()
                                )
                            )
                        )
                    ),
                ),
                Decimal("0"),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            )
        ).filter(stock_disponible_catalogo__gt=0)

        queryset = base_queryset
        if product_type:
            queryset = queryset.filter(
                Q(tipo_mascota=product_type)
                | Q(tipo_mascota__isnull=True)
                | Q(tipo_mascota="")
                | Q(tipo_mascota=Producto.TipoMascota.OTRO)
            ).annotate(
                recommendation_rank=Case(
                    When(tipo_mascota=product_type, then=Value(0)),
                    When(destacado=True, then=Value(1)),
                    default=Value(2),
                    output_field=IntegerField(),
                )
            )
        else:
            queryset = queryset.annotate(
                recommendation_rank=Case(
                    When(destacado=True, then=Value(0)),
                    default=Value(1),
                    output_field=IntegerField(),
                )
            )

        products = list(queryset.order_by("recommendation_rank", "-destacado", "-id_producto")[:limit])
        allergy_terms = cls._allergy_terms(mascota)
        return [
            {
                "producto": product,
                "motivo": cls._motivo(product, product_type),
                "advertencia": cls._advertencia(product, allergy_terms),
            }
            for product in products
        ]

    @classmethod
    def _product_type_for_pet(cls, mascota):
        species_name = getattr(getattr(mascota, "especie", None), "nombre", "") or ""
        normalized = species_name.strip().upper()
        return cls.SPECIES_TO_PRODUCT_TYPE.get(normalized)

    @classmethod
    def _motivo(cls, product, product_type):
        if product_type and product.tipo_mascota == product_type:
            return f"Recomendado para {product.get_tipo_mascota_display().lower()}."
        category_name = (getattr(product.categoria_producto, "nombre", "") or "").lower()
        if any(keyword in category_name for keyword in cls.CATEGORY_KEYWORDS):
            return f"Categoria util para el cuidado: {product.categoria_producto.nombre}."
        if product.destacado:
            return "Producto destacado del catalogo."
        return "Producto visible y disponible en el catalogo."

    @staticmethod
    def _allergy_terms(mascota):
        text = (getattr(mascota, "alergias", "") or "").replace(",", " ")
        return [part.strip().lower() for part in text.split() if len(part.strip()) >= 4]

    @staticmethod
    def _advertencia(product, allergy_terms):
        if not allergy_terms:
            return None
        haystack = f"{product.nombre} {product.descripcion or ''}".lower()
        for term in allergy_terms:
            if term in haystack:
                return f"Revisar alergia registrada: {term}."
        return None
