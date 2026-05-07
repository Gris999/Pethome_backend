from django.core.management.base import BaseCommand

from apps.AutenticacionySeguridad.services.base_access_seed_service import (
    BaseAccessSeedService,
)


class Command(BaseCommand):
    help = "Siembra/actualiza el catálogo global de componentes SaaS."

    def handle(self, *args, **options):
        result = BaseAccessSeedService.seed_global_components()
        self.stdout.write(
            self.style.SUCCESS(
                "Componentes seed finalizado | "
                f"created={result['created']} "
                f"updated={result['updated']} "
                f"total_catalog={result['total']}"
            )
        )
