from django.core.management.base import BaseCommand

from apps.GestionClientesyMascotas.services.recordatorio_notificacion_service import (
    RecordatorioNotificacionService,
)


class Command(BaseCommand):
    help = "Procesa recordatorios pendientes y genera notificaciones internas/push."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Evalua recordatorios sin guardar cambios ni enviar push.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        resumen = RecordatorioNotificacionService.procesar_pendientes(
            dry_run=dry_run,
        )
        prefix = "[DRY RUN] " if dry_run else ""
        self.stdout.write(
            self.style.SUCCESS(
                prefix
                + "Recordatorios procesados: "
                + ", ".join(f"{key}={value}" for key, value in resumen.items())
            )
        )
