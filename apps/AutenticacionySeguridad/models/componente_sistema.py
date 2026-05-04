from django.db import models


class ComponenteSistema(models.Model):
    TIPOS = [
        ("MODULO", "Modulo"),
        ("MENU", "Menu"),
        ("FORMULARIO", "Formulario"),
        ("BOTON", "Boton"),
        ("CAMPO", "Campo"),
        ("LABEL", "Label"),
        ("TEXTO", "Texto"),
        ("ACCION", "Accion"),
    ]
    PLATAFORMAS = [
        ("WEB", "Web"),
        ("MOVIL", "Movil"),
        ("AMBOS", "Ambos"),
    ]

    id_componente = models.AutoField(primary_key=True)
    codigo = models.CharField(max_length=120, unique=True)
    nombre = models.CharField(max_length=150)
    tipo = models.CharField(max_length=20, choices=TIPOS)
    modulo = models.CharField(max_length=120, blank=True, null=True)
    ruta = models.CharField(max_length=255, blank=True, null=True)
    plataforma = models.CharField(max_length=10, choices=PLATAFORMAS, default="WEB")
    padre = models.ForeignKey(
        "self",
        db_column="id_padre",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hijos",
    )
    orden = models.IntegerField(default=0)
    estado = models.BooleanField(default=True)

    class Meta:
        db_table = "componente_sistema"
        verbose_name = "Componente del sistema"
        verbose_name_plural = "Componentes del sistema"

    def __str__(self):
        return self.codigo
