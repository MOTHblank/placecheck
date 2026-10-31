import json
import time
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.listings.models import Listing
from apps.sources.models import Source


class Command(BaseCommand):
    help = "Verifica Beat/broker/worker com inventário fictício no Compose de aceite isolado."

    def handle(self, *args, **options):
        if settings.CELERY_TASK_ALWAYS_EAGER or settings.MANUAL_PROVIDER_RECORDS_FILE != "/app/.runtime/acceptance-inventory.json":
            raise CommandError("Execute apenas com docker-compose.acceptance.yml, sem eager.")
        source, _ = Source.objects.get_or_create(slug="controlled-fixture", defaults={
            "name": "DEMO — Aceite assíncrono", "provider_type": "manual",
            "is_demo": True, "is_active": False, "rate_limit_per_minute": 600,
        })
        if not source.is_demo:
            raise CommandError("Fonte de aceite deve ser fictícia.")
        source.is_active = False
        source.save()
        path = Path(settings.MANUAL_PROVIDER_RECORDS_FILE)
        path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "source_external_id": "controlled-001", "title": "DEMO Apartamento unidade 401",
            "transaction_type": "venda", "property_type": "apartamento",
            "city": "Salvador", "state": "BA", "neighborhood": "Pituba", "area": 80,
            "price": "R$ 650.000", "url": "https://controlled.example/imovel/1",
        }

        def write(records):
            temporary = path.with_suffix(".tmp")
            temporary.write_text(json.dumps({source.slug: records}), encoding="utf-8")
            temporary.replace(path)

        def wait_for(predicate):
            deadline = time.monotonic() + 45
            while time.monotonic() < deadline:
                if predicate():
                    return
                time.sleep(0.5)
            failures = list(source.sync_runs.values("id", "status", "failure")[:3])
            raise CommandError(f"Aceite assíncrono excedeu 45 s: {failures}")

        try:
            write({"controlled-001": record})
            baseline = source.sync_runs.count()
            source.is_active = True
            source.save()
            wait_for(lambda: source.sync_runs.filter(status="succeeded", processed_count=1).count() >= baseline + 2)
            listing = Listing.objects.get(source=source, external_id="controlled-001")
            initial_history_count = listing.price_history.count()
            if initial_history_count == 0:
                raise CommandError("Captura inicial não registrou histórico.")
            self.stdout.write("Beat → Redis → worker: captura e repetição concluídas.")
            record["price"] = "R$ 640.000"
            write({"controlled-001": record})
            wait_for(lambda: Listing.objects.filter(pk=listing.pk, price="640000").exists())
            if listing.price_history.count() != initial_history_count + 1:
                raise CommandError("Mudança de preço não criou exatamente um histórico.")
            write({})
            wait_for(lambda: Listing.objects.filter(pk=listing.pk, is_active=False).exists())
            self.stdout.write("Mudança de preço e ausência completa confirmadas.")
            for run in source.sync_runs.filter(status="succeeded").order_by("id"):
                self.stdout.write(f"run={run.pk} processed={run.processed_count} inactive={run.deactivated_count}")
        finally:
            source.is_active = False
            source.save()
