from django.contrib import admin
from .models import Bitacora


@admin.register(Bitacora)
class BitacoraAdmin(admin.ModelAdmin):
	list_display = (
		"id_bitacora",
		"fecha_hora",
		"veterinaria",
	)
	list_filter = ("veterinaria", "fecha_hora")
	search_fields = ("id_bitacora",)
	ordering = ("-fecha_hora",)
	readonly_fields = [field.name for field in Bitacora._meta.fields]

	def has_view_permission(self, request, obj=None):
		permiso_lectura = f"{Bitacora._meta.app_label}.view_{Bitacora._meta.model_name}"
		user = request.user
		return bool(
			user
			and user.is_active
			and (user.is_superuser or user.has_perm(permiso_lectura))
		)

	def has_add_permission(self, request):
		return False

	def has_change_permission(self, request, obj=None):
		return False

	def has_delete_permission(self, request, obj=None):
		return False
