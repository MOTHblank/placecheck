from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.ingestion.services import persist_listing
from apps.listings.models import Listing, ListingPriceHistory
from apps.sources.models import Source
from apps.sources.normalizers import normalize_listing
from apps.sources.providers import ManualProvider


LOCATIONS = (
    ("Belo Horizonte", "MG", ("Buritis", "Funcionários", "São Pedro", "Pampulha", "Centro", "Savassi"), "-19.920830", "-43.937780"),
    ("Salvador", "BA", ("Pituba", "Barra", "Stella Maris", "Itapuã", "Comércio", "Rio Vermelho"), "-12.971400", "-38.501400"),
    ("São Paulo", "SP", ("Bela Vista", "Pinheiros", "Vila Mariana", "Parelheiros", "Sé", "Moema"), "-23.550520", "-46.633308"),
    ("Rio de Janeiro", "RJ", ("Tijuca", "Botafogo", "Recreio", "Guaratiba", "Centro", "Copacabana"), "-22.906847", "-43.172897"),
    ("Curitiba", "PR", ("Centro", "Batel", "Santa Felicidade", "Umbará", "Rebouças", "Água Verde"), "-25.428400", "-49.273300"),
)
# Type, area, bedrooms, bathrooms, parking, sale price, monthly rent.
PROFILES = (
    ("apartamento", 45, 1, 1, 0, 280000, 1600),
    ("apartamento", 90, 3, 2, 2, 599000, 3600),
    ("casa", 168, 4, 3, 3, 1080000, 6200),
    ("terreno", 360, 0, 0, 0, 220000, 1200),
    ("commercial", 62, 0, 1, 1, 420000, 2800),
    ("apartamento", 140, 4, 3, 2, 1450000, 8500),
)


class Command(BaseCommand):
    help = "Carrega 30 imóveis fictícios via normalização/deduplicação, sem apagar dados existentes."

    @transaction.atomic
    def handle(self, *args, **options):
        sources = []
        for number, name in enumerate(("Horizonte", "Morada", "Lugar Certo"), start=1):
            source, _ = Source.objects.get_or_create(
                slug=f"demo-fonte-{number}",
                defaults={
                    "name": f"DEMO — {name}",
                    "provider_type": Source.ProviderType.MANUAL,
                    "base_url": f"https://fonte-{number}.example",
                    # Beat must not sync an empty manual feed and deactivate these offers.
                    "is_active": False,
                    "can_store_description": True,
                },
            )
            sources.append(source)

        created = skipped = 0
        inactive_ids = []
        now = timezone.now()
        for city_index, (city, state, neighborhoods, latitude, longitude) in enumerate(LOCATIONS):
            for profile_index, (kind, area, bedrooms, bathrooms, parking, sale, rent) in enumerate(PROFILES):
                index = city_index * len(PROFILES) + profile_index
                transaction_type = "venda" if index % 2 == 0 else "aluguel"
                base_price = sale if transaction_type == "venda" else rent
                neighborhood = neighborhoods[profile_index]
                for offer in range(index % 3 + 1):
                    source = sources[offer]
                    external_id = f"demo-{index + 1:03d}"
                    if Listing.objects.filter(source=source, external_id=external_id).exists():
                        skipped += 1
                        continue

                    price = (Decimal(base_price) * (1 + Decimal(city_index) / 10 + Decimal(offer) / 50)).quantize(Decimal("0.01"))
                    # One property has no disclosed price; others drop, rise or stay stable.
                    prices = [None] if index == 3 else {
                        0: [price * Decimal("1.08"), price * Decimal("1.03"), price],
                        1: [price * Decimal("0.95"), price * Decimal("0.98"), price],
                        2: [price],
                    }[index % 3]
                    record = {
                        "source_external_id": external_id,
                        "title": f"[DEMO] {kind.title()} em {neighborhood} — {area} m² · unidade {index + 101}",
                        "description": "Anúncio fictício para testes. Não corresponde a um imóvel real. "
                        + ("Varanda e área de lazer." if bedrooms else "Espaço para seu próximo projeto."),
                        "transaction_type": transaction_type,
                        "property_type": kind,
                        "condominium_fee": 450 + profile_index * 80 if kind == "apartamento" else 0,
                        "iptu": 80 + profile_index * 25,
                        "area": area,
                        "bedrooms": bedrooms,
                        "bathrooms": bathrooms,
                        "suites": 1 if bedrooms >= 3 else 0,
                        "parking_spaces": parking,
                        "city": city,
                        "state": state,
                        "neighborhood": neighborhood,
                        # Approximate synthetic coordinates, not real property addresses.
                        "latitude": Decimal(latitude) + Decimal(profile_index) / 1000,
                        "longitude": Decimal(longitude) + Decimal(profile_index) / 1000,
                        "url": f"{source.base_url}/imoveis/{external_id}",
                    }
                    provider = ManualProvider({external_id: record})
                    for step, historical_price in enumerate(prices):
                        record["price"] = historical_price
                        listing = persist_listing(source, normalize_listing(provider.parse(provider.fetch(external_id))))
                        if historical_price is not None:
                            history = listing.price_history.latest("id")
                            ListingPriceHistory.objects.filter(pk=history.pk).update(
                                captured_at=now - timedelta(days=(len(prices) - 1 - step) * 15),
                            )
                    first_seen = now - timedelta(days=60 + index)
                    Listing.objects.filter(pk=listing.pk).update(
                        published_at=first_seen - timedelta(days=2),
                        first_seen_at=first_seen,
                        last_seen_at=now - timedelta(hours=index),
                    )
                    if index == 29 or (index % 10 == 0 and offer == 1):
                        inactive_ids.append(listing.pk)
                    created += 1

        Listing.objects.filter(pk__in=inactive_ids).update(is_active=False)
        demo = Listing.objects.filter(source__in=sources, external_id__startswith="demo-")
        self.stdout.write(self.style.SUCCESS(
            f"DEMO: {created} anúncios criados, {skipped} existentes preservados; "
            f"{demo.values('property_id').distinct().count()} imóveis, "
            f"{demo.count()} anúncios ({demo.filter(is_active=True).count()} ativos), "
            f"{ListingPriceHistory.objects.filter(listing__in=demo).count()} registros de preço."
        ))
