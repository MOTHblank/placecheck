from dataclasses import replace
from decimal import Decimal

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from apps.ingestion.services import persist_listing
from apps.sources.models import Source
from apps.sources.normalizers import normalize_listing
from apps.sources.providers import ManualProvider


class Command(BaseCommand):
    help = "Prepara fixtures de navegador exclusivamente no stack de aceite isolado."

    def handle(self, *args, **options):
        if settings.MANUAL_PROVIDER_RECORDS_FILE != "/app/.runtime/acceptance-inventory.json":
            raise CommandError("Use o Compose de aceite isolado.")
        call_command("seed_demo")
        sources = [Source.objects.get_or_create(slug=f"browser-fixture-{index}", defaults={
            "name": f"TEST — publicação simulada {index}", "provider_type": "manual",
            "is_active": False, "can_store_description": True,
        })[0] for index in (1, 2)]
        for index in range(14):
            raw = ManualProvider({}).parse({
                "source_external_id": f"browser-{index}", "title": f"Apartamento Testópolis unidade {100 + index}",
                "description": "Fixture local; destino externo será interceptado no teste.",
                "transaction_type": "sale", "property_type": "apartment", "area": 80,
                "bedrooms": 3, "price": "R$ 650.000", "city": "Testópolis", "state": "BA",
                "neighborhood": f"Bairro {index}", "latitude": Decimal("-12.9") + Decimal(index) / 1000,
                "longitude": "-38.5", "url": f"https://fixture.invalid/oferta/{index}",
            })
            normalized = normalize_listing(raw)
            for source in sources:
                persist_listing(source, normalized)
                persist_listing(source, replace(normalized, price=Decimal("640000")))
        self.stdout.write("14 imóveis/28 ofertas em Testópolis; fixtures sem contato externo.")
