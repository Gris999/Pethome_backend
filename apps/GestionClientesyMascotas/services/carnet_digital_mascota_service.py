from apps.GestionarClinicaVeterinaria.models import (
    HistorialClinico,
    PlanSanitarioPreventivo,
    VacunaAplicada,
)
from django.conf import settings
from django.core import signing
from urllib.parse import urlencode

from apps.GestionClientesyMascotas.models import Mascota


PUBLIC_CARNET_SALT = "pethome.public.pet-card"


class CarnetDigitalMascotaService:
    @staticmethod
    def _clean_text(value):
        if not isinstance(value, str) or not any(marker in value for marker in ("Ã", "Â")):
            return value
        try:
            return value.encode("latin1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            return value

    @staticmethod
    def build_payload(*, mascota, request=None):
        usuario = mascota.usuario
        perfil = getattr(usuario, "perfil", None)
        veterinaria = mascota.veterinaria
        frontend_base_url = getattr(
            settings,
            "FRONTEND_BASE_URL",
            "https://pet-home-blond.vercel.app",
        ).rstrip("/")
        public_token = signing.dumps(
            {
                "pet": mascota.id_mascota,
                "vet": veterinaria.id_veterinaria,
            },
            salt=PUBLIC_CARNET_SALT,
        )
        qr_url = (
            f"{frontend_base_url}/carnet-mascota?"
            f"{urlencode({'token': public_token})}"
        )
        historial = (
            HistorialClinico.objects.filter(mascota=mascota, estado=True)
            .prefetch_related("consultas_clinicas")
            .first()
        )

        vacunas = VacunaAplicada.objects.none()
        consultas_count = 0
        ultima_consulta = None
        if historial:
            consultas = historial.consultas_clinicas.filter(estado=True)
            consultas_count = consultas.count()
            ultima = consultas.order_by("-fecha_consulta").first()
            ultima_consulta = ultima.fecha_consulta.date().isoformat() if ultima else None
            vacunas = VacunaAplicada.objects.filter(
                consulta_clinica__historial_clinico=historial,
                estado=True,
            ).order_by("-fecha_aplicada")[:8]

        pendientes = PlanSanitarioPreventivo.objects.filter(
            mascota=mascota,
            veterinaria=veterinaria,
            estado=True,
            estado_plan=PlanSanitarioPreventivo.EstadoPlanChoices.PENDIENTE,
        ).order_by("fecha_programada")[:8]

        return {
            "mascota": {
                "id_mascota": mascota.id_mascota,
                "nombre": mascota.nombre,
                "especie": getattr(mascota.especie, "nombre", None),
                "raza": getattr(mascota.raza, "nombre", None),
                "sexo": mascota.sexo,
                "fecha_nac": mascota.fecha_nac.isoformat() if mascota.fecha_nac else None,
                "color": mascota.color,
                "peso": str(mascota.peso) if mascota.peso is not None else None,
                "tamano": mascota.tamano,
                "foto": mascota.foto,
                "alergias": mascota.alergias,
                "notas_generales": mascota.notas_generales,
            },
            "duenio": {
                "id_usuario": usuario.id_usuario,
                "correo": usuario.correo,
                "nombre": getattr(perfil, "nombre", None) or usuario.correo,
                "telefono": getattr(perfil, "telefono", None),
            },
            "veterinaria": {
                "id_veterinaria": veterinaria.id_veterinaria,
                "nombre": veterinaria.nombre,
                "slug": veterinaria.slug,
            },
            "vacunas_aplicadas": [
                {
                    "id_vacuna_aplicada": vacuna.id_vacuna_aplicada,
                    "nombre_vacuna": CarnetDigitalMascotaService._clean_text(
                        vacuna.nombre_vacuna
                    ),
                    "dosis": vacuna.dosis,
                    "fecha_aplicada": vacuna.fecha_aplicada.isoformat(),
                    "fecha_proxima": vacuna.fecha_proxima.isoformat()
                    if vacuna.fecha_proxima
                    else None,
                    "estado_vacuna": vacuna.estado_vacuna,
                }
                for vacuna in vacunas
            ],
            "historial_resumen": {
                "tiene_historial": historial is not None,
                "total_consultas": consultas_count,
                "ultima_consulta": ultima_consulta,
                "observaciones_generales": CarnetDigitalMascotaService._clean_text(
                    getattr(historial, "observaciones_generales", None)
                ),
            },
            "plan_sanitario_pendiente": [
                {
                    "id_plan_sanitario": item.id_plan_sanitario,
                    "tipo_evento": item.tipo_evento,
                    "tipo_evento_display": item.get_tipo_evento_display(),
                    "descripcion": CarnetDigitalMascotaService._clean_text(
                        item.descripcion
                    ),
                    "fecha_programada": item.fecha_programada.isoformat(),
                    "estado_plan": item.estado_plan,
                }
                for item in pendientes
            ],
            "qr_payload": (
                f"PETHOME:PET:{mascota.id_mascota}:VET:{veterinaria.id_veterinaria}"
            ),
            "qr_url": qr_url,
            "qr_token": public_token,
        }

    @staticmethod
    def build_public_payload(*, token):
        data = signing.loads(token, salt=PUBLIC_CARNET_SALT)
        mascota = Mascota.objects.select_related("veterinaria", "especie", "raza").get(
            id_mascota=data["pet"],
            veterinaria_id=data["vet"],
            estado=True,
        )
        full_payload = CarnetDigitalMascotaService.build_payload(mascota=mascota)
        return {
            "mascota": {
                "nombre": full_payload["mascota"]["nombre"],
                "especie": full_payload["mascota"]["especie"],
                "raza": full_payload["mascota"]["raza"],
                "sexo": full_payload["mascota"]["sexo"],
                "fecha_nac": full_payload["mascota"]["fecha_nac"],
                "color": full_payload["mascota"]["color"],
                "peso": full_payload["mascota"]["peso"],
                "tamano": full_payload["mascota"]["tamano"],
            },
            "veterinaria": full_payload["veterinaria"],
            "vacunas_aplicadas": full_payload["vacunas_aplicadas"],
            "proximos_cuidados": full_payload["plan_sanitario_pendiente"],
            "estado": "VALIDO",
        }
