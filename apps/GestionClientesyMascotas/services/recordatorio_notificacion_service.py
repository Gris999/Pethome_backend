from datetime import datetime, time, timedelta

from django.db import transaction
from django.utils import timezone

from apps.GestionClientesyMascotas.models import RecordatorioMascota
from apps.NotificacionesySeguimiento.models import DispositivoUsuario, Notificacion
from apps.NotificacionesySeguimiento.services.notification_service import (
    NotificationService,
)


class RecordatorioNotificacionService:
    MAX_INTENTOS = 3

    TIPO_NOTIFICACION = {
        RecordatorioMascota.TipoRecordatorio.VACUNA: Notificacion.TipoNotificacion.VACUNA,
        RecordatorioMascota.TipoRecordatorio.CONTROL: Notificacion.TipoNotificacion.CONTROL,
    }

    @classmethod
    def procesar_pendientes(cls, *, now=None, dry_run=False):
        now = now or timezone.now()
        resumen = {
            "evaluados": 0,
            "creados": 0,
            "push_enviados": 0,
            "sin_dispositivo": 0,
            "fallidos": 0,
            "vencidos": 0,
        }
        ids = list(
            RecordatorioMascota.objects.filter(
                estado=RecordatorioMascota.EstadoRecordatorio.PENDIENTE,
            ).values_list("id_recordatorio", flat=True)
        )

        for recordatorio_id in ids:
            resultado = cls._procesar_uno(
                recordatorio_id=recordatorio_id,
                now=now,
                dry_run=dry_run,
            )
            if not resultado:
                continue
            resumen["evaluados"] += 1
            for key in resultado:
                if key in resumen:
                    resumen[key] += 1
        return resumen

    @classmethod
    @transaction.atomic
    def _procesar_uno(cls, *, recordatorio_id, now, dry_run):
        recordatorio = (
            RecordatorioMascota.objects.select_for_update()
            .select_related("mascota", "usuario", "veterinaria")
            .filter(
                id_recordatorio=recordatorio_id,
                estado=RecordatorioMascota.EstadoRecordatorio.PENDIENTE,
            )
            .first()
        )
        if not recordatorio:
            return None

        fecha_evento = cls._fecha_evento(recordatorio)
        fecha_aviso = fecha_evento - timedelta(days=recordatorio.dias_anticipacion)
        vencido = fecha_evento < now
        resultado = {}

        if recordatorio.notificar and fecha_aviso <= now:
            if (
                recordatorio.fecha_notificacion_enviada is None
                and recordatorio.intentos_notificacion < cls.MAX_INTENTOS
            ):
                if dry_run:
                    resultado["creados"] = True
                else:
                    notificacion, creada = cls._obtener_o_crear_notificacion(
                        recordatorio=recordatorio,
                        vencido=vencido,
                    )
                    if creada:
                        resultado["creados"] = True

                    tiene_dispositivos = DispositivoUsuario.objects.filter(
                        usuario=recordatorio.usuario,
                        activo=True,
                    ).exists()
                    recordatorio.intentos_notificacion += 1
                    try:
                        enviada = NotificationService.enviar_notificacion_push(notificacion)
                        if enviada:
                            resultado["push_enviados"] = True
                            recordatorio.ultimo_error_notificacion = None
                            recordatorio.fecha_notificacion_enviada = timezone.now()
                        elif not tiene_dispositivos:
                            resultado["sin_dispositivo"] = True
                            recordatorio.ultimo_error_notificacion = (
                                "Notificacion interna creada; no hay dispositivo FCM activo."
                            )
                            recordatorio.fecha_notificacion_enviada = timezone.now()
                        else:
                            resultado["fallidos"] = True
                            recordatorio.ultimo_error_notificacion = (
                                "Firebase no confirmo ningun envio exitoso."
                            )
                    except Exception as error:
                        resultado["fallidos"] = True
                        recordatorio.ultimo_error_notificacion = str(error)[:1000]

                    recordatorio.save(
                        update_fields=[
                            "notificacion",
                            "fecha_notificacion_enviada",
                            "intentos_notificacion",
                            "ultimo_error_notificacion",
                            "fecha_actualizacion",
                        ]
                    )

        if vencido:
            resultado["vencidos"] = True
            if not dry_run:
                recordatorio.estado = RecordatorioMascota.EstadoRecordatorio.VENCIDO
                recordatorio.save(update_fields=["estado", "fecha_actualizacion"])

        return resultado

    @classmethod
    def _obtener_o_crear_notificacion(cls, *, recordatorio, vencido):
        if recordatorio.notificacion_id:
            return recordatorio.notificacion, False

        tipo = cls.TIPO_NOTIFICACION.get(
            recordatorio.tipo,
            Notificacion.TipoNotificacion.SISTEMA,
        )
        prefijo = "Recordatorio vencido" if vencido else "Recordatorio"
        mensaje = (
            f"{recordatorio.mascota.nombre}: {recordatorio.titulo}. "
            f"Fecha: {recordatorio.fecha_programada:%d/%m/%Y}."
        )
        notificacion = NotificationService.crear_notificacion(
            usuario=recordatorio.usuario,
            titulo=f"{prefijo}: {recordatorio.titulo}",
            mensaje=mensaje,
            tipo=tipo,
            id_entidad=recordatorio.id_recordatorio,
        )
        notificacion.link = (
            f"/mascotas/{recordatorio.mascota_id}/recordatorios/"
        )
        notificacion.save(update_fields=["link"])
        recordatorio.notificacion = notificacion
        recordatorio.save(update_fields=["notificacion", "fecha_actualizacion"])
        return notificacion, True

    @staticmethod
    def _fecha_evento(recordatorio):
        hora = recordatorio.hora_programada or time(hour=9)
        value = datetime.combine(recordatorio.fecha_programada, hora)
        if timezone.is_naive(value):
            value = timezone.make_aware(value, timezone.get_current_timezone())
        return value
