from django.core.management.base import BaseCommand, CommandError

from apps.AutenticacionySeguridad.models import Veterinaria
from apps.AutenticacionySeguridad.services.base_access_seed_service import (
    BaseAccessSeedService,
)


class Command(BaseCommand):
    help = (
        "Siembra grupos base y permisos base por veterinaria. "
        "Opcionalmente asigna usuarios existentes a su grupo base."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--veterinaria-id",
            type=int,
            default=None,
            help="ID de veterinaria específica. Si no se envía, aplica a todas.",
        )
        parser.add_argument(
            "--assign-existing-users",
            action="store_true",
            help="Asigna usuarios existentes al grupo base según su rol.",
        )

    def handle(self, *args, **options):
        vet_id = options.get("veterinaria_id")
        assign_existing = options.get("assign_existing_users", False)

        if vet_id:
            veterinarias = Veterinaria.objects.filter(pk=vet_id)
            if not veterinarias.exists():
                raise CommandError(f"No existe veterinaria con id={vet_id}")
        else:
            veterinarias = Veterinaria.objects.all()
            if not veterinarias.exists():
                raise CommandError("No hay veterinarias registradas.")

        result = BaseAccessSeedService.seed_for_veterinarias(
            veterinarias=veterinarias, assign_existing=assign_existing
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Seed de grupos/permisos base finalizado | "
                f"veterinarias={result['veterinarias']} "
                f"groups_created={result['groups_created']} "
                f"permissions_created={result['permissions_created']} "
                f"assignments_created={result['assignments_created']}"
            )
        )
