from datetime import date, datetime, time, timedelta
from unittest.mock import patch

from django.test import override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.AutenticacionySeguridad.enums.roles import RoleEnum
from apps.AutenticacionySeguridad.models import (
	ComponenteSistema,
	GrupoPermisoComponente,
	GrupoUsuario,
	Perfil,
	Rol,
	User,
	UsuarioGrupo,
	Veterinaria,
)
from apps.GestionClientesyMascotas.models import (
	Especie,
	Mascota,
	Raza,
	RecordatorioMascota,
	RegistroEvolucionMascota,
)
from apps.GestionClientesyMascotas.services.recordatorio_notificacion_service import (
	RecordatorioNotificacionService,
)
from apps.NotificacionesySeguimiento.models import Notificacion

FERNET_TEST_KEY = "y-8vRXvZL5t7I8S_dZd2a0B7aKXzH_kL8BkpE9SLiW8="


@override_settings(BITACORA_SECRET_KEYS=[FERNET_TEST_KEY])
class MascotaTenantTests(APITestCase):
	def setUp(self):
		self.vet_a = Veterinaria.objects.create(
			nombre="Vet A",
			slug="vet-a",
			nit="111",
			correo="vet-a@example.com",
		)
		self.vet_b = Veterinaria.objects.create(
			nombre="Vet B",
			slug="vet-b",
			nit="222",
			correo="vet-b@example.com",
		)

		self.rol_admin = Rol.objects.create(
			nombre=RoleEnum.ADMIN.value,
			descripcion="Administrador",
		)
		self.rol_client = Rol.objects.create(
			nombre=RoleEnum.CLIENT.value,
			descripcion="Cliente",
		)

		self.admin_a = User.objects.create(
			correo="admin-a@example.com",
			role=self.rol_admin,
			veterinaria=self.vet_a,
			is_active=True,
			is_staff=True,
			is_superuser=True,
		)
		self.admin_a.set_password("Admin12345!")
		self.admin_a.save()

		self.admin_b = User.objects.create(
			correo="admin-b@example.com",
			role=self.rol_admin,
			veterinaria=self.vet_b,
			is_active=True,
			is_staff=True,
			is_superuser=True,
		)
		self.admin_b.set_password("Admin12345!")
		self.admin_b.save()

		self.client_a = User.objects.create(
			correo="cliente-a@example.com",
			role=self.rol_client,
			veterinaria=self.vet_a,
			is_active=True,
			is_staff=False,
			is_superuser=False,
		)
		self.client_b = User.objects.create(
			correo="cliente-b@example.com",
			role=self.rol_client,
			veterinaria=self.vet_b,
			is_active=True,
			is_staff=False,
			is_superuser=False,
		)

		self.especie = Especie.objects.create(nombre="Canino")
		self.raza = Raza.objects.create(nombre="Labrador", especie=self.especie)

		self.mascota_a = Mascota.objects.create(
			usuario=self.client_a,
			especie=self.especie,
			raza=self.raza,
			veterinaria=self.vet_a,
			nombre="Firulais",
			fecha_nac=date(2023, 1, 1),
		)
		self.mascota_b = Mascota.objects.create(
			usuario=self.client_b,
			especie=self.especie,
			raza=self.raza,
			veterinaria=self.vet_b,
			nombre="Luna",
			fecha_nac=date(2023, 2, 1),
		)
		self.comp_mascotas = ComponenteSistema.objects.create(
			codigo="CLI_MASCOTAS",
			nombre="Mascotas",
			tipo="MODULO",
			modulo="CLIENTES",
			ruta="/mascotas",
			plataforma="WEB",
			estado=True,
		)
		self.client_group_a = GrupoUsuario.objects.create(
			nombre="Clientes Vet A",
			descripcion="Permisos clientes vet A",
			estado=True,
			veterinaria=self.vet_a,
		)
		UsuarioGrupo.objects.create(usuario=self.client_a, grupo=self.client_group_a, estado=True)
		GrupoPermisoComponente.objects.create(
			grupo=self.client_group_a,
			componente=self.comp_mascotas,
			puede_ver=True,
			estado=True,
		)

	def test_mascotas_list_is_tenant_scoped(self):
		self.client.force_login(self.admin_a)
		response = self.client.get("/api/gestion/clientes/mascotas/")
		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.data), 1)
		self.assertEqual(response.data[0]["id_mascota"], self.mascota_a.id_mascota)

		self.client.force_login(self.admin_b)
		response = self.client.get("/api/gestion/clientes/mascotas/")
		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.data), 1)
		self.assertEqual(response.data[0]["id_mascota"], self.mascota_b.id_mascota)

	def test_mascota_detail_other_tenant_returns_404(self):
		self.client.force_login(self.admin_a)
		response = self.client.get(
			f"/api/gestion/clientes/mascotas/{self.mascota_b.id_mascota}/"
		)
		self.assertEqual(response.status_code, 404)

	def test_cliente_only_sees_own_mascotas(self):
		self.client.force_login(self.client_a)
		response = self.client.get("/api/gestion/clientes/mascotas/")
		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.data), 1)
		self.assertEqual(response.data[0]["id_mascota"], self.mascota_a.id_mascota)

	def test_perfil_seguimiento_blocks_other_tenant_and_allows_owner(self):
		self.client.force_login(self.client_a)
		own_response = self.client.get(
			f"/api/gestion/clientes/mascotas/{self.mascota_a.id_mascota}/perfil-seguimiento/"
		)
		self.assertEqual(own_response.status_code, 200)
		self.assertEqual(own_response.data["id_mascota"], self.mascota_a.id_mascota)

		other_response = self.client.get(
			f"/api/gestion/clientes/mascotas/{self.mascota_b.id_mascota}/perfil-seguimiento/"
		)
		self.assertEqual(other_response.status_code, 404)

	def test_recordatorios_create_list_complete_cancel_and_scope_owner(self):
		self.client.force_login(self.client_a)
		create_response = self.client.post(
			f"/api/gestion/clientes/mascotas/{self.mascota_a.id_mascota}/recordatorios/",
			{
				"tipo": "VACUNA",
				"titulo": "Vacuna antirrabica",
				"descripcion": "Aplicar refuerzo anual",
				"fecha_programada": "2026-07-20",
				"hora_programada": "09:30:00",
				"notificar": True,
				"dias_anticipacion": 2,
			},
			format="json",
		)
		self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
		recordatorio_id = create_response.data["id_recordatorio"]
		recordatorio = RecordatorioMascota.objects.get(pk=recordatorio_id)
		self.assertEqual(recordatorio.usuario_id, self.client_a.id_usuario)
		self.assertEqual(recordatorio.veterinaria_id, self.vet_a.id_veterinaria)

		list_response = self.client.get(
			f"/api/gestion/clientes/mascotas/{self.mascota_a.id_mascota}/recordatorios/"
		)
		self.assertEqual(list_response.status_code, status.HTTP_200_OK)
		self.assertEqual(len(list_response.data), 1)
		self.assertEqual(list_response.data[0]["titulo"], "Vacuna antirrabica")

		complete_response = self.client.post(
			f"/api/gestion/clientes/recordatorios/{recordatorio_id}/completar/"
		)
		self.assertEqual(complete_response.status_code, status.HTTP_200_OK)
		self.assertEqual(complete_response.data["estado"], "COMPLETADO")

		cancel_response = self.client.post(
			f"/api/gestion/clientes/recordatorios/{recordatorio_id}/cancelar/"
		)
		self.assertEqual(cancel_response.status_code, status.HTTP_200_OK)
		self.assertEqual(cancel_response.data["estado"], "CANCELADO")

		other_pet_response = self.client.get(
			f"/api/gestion/clientes/mascotas/{self.mascota_b.id_mascota}/recordatorios/"
		)
		self.assertEqual(other_pet_response.status_code, status.HTTP_404_NOT_FOUND)

	def test_carnet_digital_returns_payload_and_blocks_other_pet(self):
		self.client.force_login(self.client_a)
		response = self.client.get(
			f"/api/gestion/clientes/mascotas/{self.mascota_a.id_mascota}/carnet-digital/"
		)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data["mascota"]["id_mascota"], self.mascota_a.id_mascota)
		self.assertEqual(response.data["duenio"]["id_usuario"], self.client_a.id_usuario)
		self.assertEqual(response.data["veterinaria"]["id_veterinaria"], self.vet_a.id_veterinaria)
		self.assertIn("qr_payload", response.data)

		other_response = self.client.get(
			f"/api/gestion/clientes/mascotas/{self.mascota_b.id_mascota}/carnet-digital/"
		)
		self.assertEqual(other_response.status_code, status.HTTP_404_NOT_FOUND)

	@patch(
		"apps.GestionClientesyMascotas.services.recordatorio_notificacion_service."
		"NotificationService.enviar_notificacion_push",
		return_value=False,
	)
	def test_recordatorio_notification_is_persistent_and_idempotent(self, push_mock):
		now = timezone.make_aware(datetime(2026, 7, 10, 10, 0))
		recordatorio = RecordatorioMascota.objects.create(
			mascota=self.mascota_a,
			usuario=self.client_a,
			veterinaria=self.vet_a,
			tipo=RecordatorioMascota.TipoRecordatorio.VACUNA,
			titulo="Refuerzo anual",
			fecha_programada=(now + timedelta(days=1)).date(),
			hora_programada=time(10, 0),
			notificar=True,
			dias_anticipacion=1,
		)

		first = RecordatorioNotificacionService.procesar_pendientes(now=now)
		second = RecordatorioNotificacionService.procesar_pendientes(now=now)
		recordatorio.refresh_from_db()

		self.assertEqual(first["creados"], 1)
		self.assertEqual(second["creados"], 0)
		self.assertEqual(recordatorio.intentos_notificacion, 1)
		self.assertIsNotNone(recordatorio.fecha_notificacion_enviada)
		self.assertEqual(
			Notificacion.objects.filter(
				usuario=self.client_a,
				id_entidad_relacionada=recordatorio.id_recordatorio,
			).count(),
			1,
		)
		push_mock.assert_called_once()

	def test_evolucion_create_update_delete_and_validate_weight(self):
		self.client.force_login(self.client_a)
		invalid_response = self.client.post(
			f"/api/gestion/clientes/mascotas/{self.mascota_a.id_mascota}/evolucion/",
			{
				"peso": "0",
				"condicion_corporal": "NORMAL",
				"nota": "Peso invalido",
				"fecha_registro": "2026-07-06",
			},
			format="json",
		)
		self.assertEqual(invalid_response.status_code, status.HTTP_400_BAD_REQUEST)

		create_response = self.client.post(
			f"/api/gestion/clientes/mascotas/{self.mascota_a.id_mascota}/evolucion/",
			{
				"peso": "8.40",
				"condicion_corporal": "NORMAL",
				"nota": "Come mejor",
				"fecha_registro": "2026-07-06",
			},
			format="json",
		)
		self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
		registro_id = create_response.data["id_registro"]
		registro = RegistroEvolucionMascota.objects.get(pk=registro_id)
		self.assertEqual(registro.usuario_id, self.client_a.id_usuario)
		self.assertEqual(registro.veterinaria_id, self.vet_a.id_veterinaria)

		list_response = self.client.get(
			f"/api/gestion/clientes/mascotas/{self.mascota_a.id_mascota}/evolucion/"
		)
		self.assertEqual(list_response.status_code, status.HTTP_200_OK)
		self.assertEqual(len(list_response.data), 1)

		update_response = self.client.patch(
			f"/api/gestion/clientes/evolucion/{registro_id}/",
			{"peso": "8.90", "condicion_corporal": "SOBREPESO"},
			format="json",
		)
		self.assertEqual(update_response.status_code, status.HTTP_200_OK)
		self.assertEqual(update_response.data["condicion_corporal"], "SOBREPESO")

		delete_response = self.client.delete(
			f"/api/gestion/clientes/evolucion/{registro_id}/"
		)
		self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)

		other_pet_response = self.client.get(
			f"/api/gestion/clientes/mascotas/{self.mascota_b.id_mascota}/evolucion/"
		)
		self.assertEqual(other_pet_response.status_code, status.HTTP_404_NOT_FOUND)


@override_settings(BITACORA_SECRET_KEYS=[FERNET_TEST_KEY])
class ClienteManagementTests(APITestCase):
	def setUp(self):
		self.vet = Veterinaria.objects.create(
			nombre="Vet CU7",
			slug="vet-cu7",
			nit="777",
			correo="vet-cu7@example.com",
		)
		self.rol_admin = Rol.objects.create(
			nombre=RoleEnum.ADMIN.value,
			descripcion="Administrador",
		)
		self.rol_client = Rol.objects.create(
			nombre=RoleEnum.CLIENT.value,
			descripcion="Cliente",
		)

		self.admin = User.objects.create(
			correo="admin-cu7@example.com",
			role=self.rol_admin,
			veterinaria=self.vet,
			is_active=True,
			is_staff=True,
			is_superuser=True,
		)
		self.admin.set_password("Admin12345!")
		self.admin.save()

		self.no_admin = User.objects.create(
			correo="noadmin-cu7@example.com",
			role=self.rol_client,
			veterinaria=self.vet,
			is_active=True,
			is_staff=False,
			is_superuser=False,
		)
		self.no_admin.set_password("Admin12345!")
		self.no_admin.save()
		Perfil.objects.create(
			usuario=self.no_admin,
			nombre="Cliente No Admin",
			telefono="70000010",
			direccion="Zona Centro",
		)

		self.client_user = User.objects.create(
			correo="cliente-existente-cu7@example.com",
			role=self.rol_client,
			veterinaria=self.vet,
			is_active=True,
			is_staff=False,
			is_superuser=False,
		)
		self.client_user.set_password("Admin12345!")
		self.client_user.save()
		self.client_profile = Perfil.objects.create(
			usuario=self.client_user,
			nombre="Cliente Existente",
			telefono="70000011",
			direccion="Zona Sur",
		)

	def test_admin_can_list_clients(self):
		self.client.force_login(self.admin)
		response = self.client.get("/api/gestion/clientes/clientes/")
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertIn("results", response.data)
		self.assertGreaterEqual(len(response.data["results"]), 1)

	def test_admin_can_create_edit_and_deactivate_client(self):
		self.client.force_login(self.admin)
		create_payload = {
			"correo": "nuevo-cliente-cu7@example.com",
			"password": "Cliente123!",
			"nombre": "Nuevo Cliente",
			"telefono": "70000012",
			"direccion": "Zona Norte",
			"estado": True,
		}
		create_response = self.client.post(
			"/api/gestion/clientes/clientes/",
			create_payload,
			format="json",
		)
		self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
		perfil_id = create_response.data["id_perfil"]
		user_id = create_response.data["usuario"]

		edit_response = self.client.patch(
			f"/api/gestion/clientes/clientes/{perfil_id}/",
			{"nombre": "Cliente Editado CU7"},
			format="json",
		)
		self.assertEqual(edit_response.status_code, status.HTTP_200_OK)
		self.assertEqual(edit_response.data["nombre"], "Cliente Editado CU7")

		delete_response = self.client.delete(f"/api/gestion/clientes/clientes/{perfil_id}/")
		self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
		self.assertFalse(User.objects.get(pk=user_id).is_active)

	def test_create_client_validates_required_fields(self):
		self.client.force_login(self.admin)
		response = self.client.post(
			"/api/gestion/clientes/clientes/",
			{
				"correo": "cliente-sin-nombre-cu7@example.com",
				"password": "Cliente123!",
				"telefono": "70000013",
				"direccion": "Sin nombre",
			},
			format="json",
		)
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn("nombre", response.data)

	def test_create_client_prevents_duplicate_email(self):
		self.client.force_login(self.admin)
		response = self.client.post(
			"/api/gestion/clientes/clientes/",
			{
				"correo": self.client_user.correo,
				"password": "Cliente123!",
				"nombre": "Duplicado",
				"telefono": "70000014",
				"direccion": "Zona Duplicada",
			},
			format="json",
		)
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn("correo", response.data)

	def test_non_admin_cannot_access_client_management(self):
		self.client.force_login(self.no_admin)
		response = self.client.get("/api/gestion/clientes/clientes/")
		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
