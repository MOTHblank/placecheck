from django.db import transaction

from apps.listings.models import Listing, ListingPriceHistory
from apps.deduplication.services import match_listing_to_property
from apps.sources.normalizers import normalize_listing
from apps.sources.providers import ListingProvider
from apps.sources.schemas import NormalizedListing
from apps.sources.models import Source
from apps.properties.services import refresh_property


@transaction.atomic
def persist_listing(source, listing: NormalizedListing) -> Listing:
    # Serialize first inserts as well as updates from the same source. An absent
    # listing row cannot be locked; the source lock closes that race.
    Source.objects.select_for_update().get(pk=source.pk)
    values = {
        "title": listing.title,
        "description": listing.description,
        "transaction_type": listing.transaction_type,
        "property_type": listing.property_type,
        "price": listing.price,
        "condominium_fee": listing.condominium_fee,
        "iptu": listing.iptu,
        "area": listing.area,
        "bedrooms": listing.bedrooms,
        "bathrooms": listing.bathrooms,
        "suites": listing.suites,
        "parking_spaces": listing.parking_spaces,
        "city": listing.city,
        "state": listing.state,
        "neighborhood": listing.neighborhood,
        "latitude": listing.latitude,
        "longitude": listing.longitude,
        "url": listing.url,
        "is_active": True,
    }
    existing = Listing.objects.select_for_update(no_key=True).filter(
        source=source,
        external_id=listing.source_external_id,
    ).first()
    previous_price = existing.price if existing else None
    # The source lock also protects absent rows. Keep NO KEY UPDATE for existing
    # offers so concurrent match audits may reference them without deadlocking.
    created = existing is None
    if created:
        persisted = Listing.objects.create(source=source, external_id=listing.source_external_id, **values)
    else:
        persisted = existing
        for field, value in values.items():
            setattr(persisted, field, value)
        persisted.save(update_fields=[*values, "last_seen_at", "updated_at"])
    if persisted.price is not None and (created or previous_price != persisted.price):
        ListingPriceHistory.objects.create(listing=persisted, price=persisted.price)
    match_listing_to_property(persisted)
    return persisted


@transaction.atomic
def ingest_provider(source, provider: ListingProvider) -> list[Listing]:
    """Executa coleta, parsing, normalização e persistência fora do provider."""
    persisted = []
    for reference in provider.discover():
        raw_listing = provider.parse(provider.fetch(reference))
        normalized_listing = normalize_listing(raw_listing)
        persisted.append(persist_listing(source, normalized_listing))
    reconcile_source_listings(source, [listing.external_id for listing in persisted])
    return persisted


@transaction.atomic
def reconcile_source_listings(source, seen_external_ids: list[str]) -> int:
    """Desativa anúncios ativos que não apareceram nesta sincronização."""
    queryset = Listing.objects.filter(source=source, is_active=True)
    if seen_external_ids:
        queryset = queryset.exclude(external_id__in=seen_external_ids)
    property_ids = list(queryset.exclude(property_id=None).values_list("property_id", flat=True).distinct())
    count = queryset.update(is_active=False)
    for property_id in sorted(set(property_ids)):
        refresh_property(property_id)
    return count
