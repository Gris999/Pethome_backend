from django.db import models

class Rol(models.Model):
    class RolName(models.TextChoices):
        SUPERADMIN = "SUPERADMIN", "Superadministrador"
        ADMIN = "ADMIN", "Administrador"
        VETERINARIAN = "VETERINARIAN", "Veterinario"
        RECEPCIONISTA = "RECEPCIONISTA", "Recepcionista"
        CLIENT = "CLIENT", "Cliente"

    id_rol = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50, unique=True, choices=RolName.choices)
    descripcion = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "roles"
        verbose_name = "Rol"
        verbose_name_plural = "Roles"

    def __str__(self):
        return self.nombre
    
