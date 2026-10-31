from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.listings.models import Listing
from apps.properties.models import Property
from apps.sources.models import Source


class Command(BaseCommand):
    help = "Fixtures aritméticas de analytics, somente no stack isolado de aceitação."

    def handle(self, *args, **options):
        if settings.MANUAL_PROVIDER_RECORDS_FILE != "/app/.runtime/acceptance-inventory.json":
            raise CommandError("Use o Compose isolado de aceitação.")
        for device in ("desktop", "mobile"):
            source, _ = Source.objects.update_or_create(slug=f"analytics-test-{device}", defaults={
                "name": f"TEST analytics {device}", "provider_type": "manual", "is_active": False,
                "is_published": True, "is_demo": False, "can_retain_analytics": True,
                "can_store_description": True,
            })
            listing = source.listings.first()
            property_ = listing.property if listing else Property.objects.create(
                city=f"Metricópolis {device}", state="BA", neighborhood="Fixture", property_type="apartment")
            # Manual fixture: deliberately shared Property, independent of matching quality.
            for index in range(3):
                Listing.objects.update_or_create(source=source, external_id=f"metric-{index}", defaults={
                    "property": property_, "city": property_.city, "state": "BA", "neighborhood": "Fixture",
                    "property_type": "apartment", "transaction_type": "sale", "is_active": True,
                    "title": f"Oferta sintética {index}", "price": 100000 + index * 1000,
                    "description": "Fixture de visibilidade; não representa inventário real. " * 100,
                    "url": f"https://fixture.invalid/analytics/{device}/{index}",
                })
        self.stdout.write("Fixtures de analytics preparadas; não são fontes reais.")
