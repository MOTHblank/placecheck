from django.core.management.base import BaseCommand
from apps.deduplication.services import match_listing_to_property
from apps.listings.models import Listing


class Command(BaseCommand):
    help = "Reavalia associações de anúncios ativos e registra as decisões."

    def handle(self, *args, **options):
        count = 0
        for listing in Listing.objects.filter(is_active=True).order_by("id").iterator():
            match_listing_to_property(listing)
            count += 1
        self.stdout.write(self.style.SUCCESS(f"{count} anúncios reavaliados."))
