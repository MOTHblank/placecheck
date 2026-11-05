from django.db import transaction

from apps.listings.models import Listing, ListingPriceHistory
from apps.deduplication.services import match_listing_to_property
from apps.sources.normalizers import normalize_listing
from apps.sources.providers import ListingProvider
from apps.sources.schemas import NormalizedListing
from apps.sources.models import Source
from apps.properties.services import refresh_property
from apps.ingestion.runs import current_run, fail_run, record_discovery, start_run
from django.utils import timezone


@transaction.atomic
def persist_listing(source, listing: NormalizedListing, *, run_id=None) -> Listing | None:
    # Serialize first inserts as well as updates from the same source. An absent
    # listing row cannot be locked; the source lock closes that race.
    source = Source.objects.select_for_update().get(pk=source.pk)
    run = current_run(source, run_id) if run_id else None
    if run_id and (run is None or run.status != "running" or not source.is_active):
        return None
    values = {
        "title": listing.title,
        "description": listing.description if source.can_store_description else "",
        "transaction_type": listing.transaction_type,
        "property_type": listing.property_type,
        "price": listing.price,
        "sale_method": listing.sale_method,
        "price_kind": listing.price_kind,
        "source_inventory_date": listing.source_inventory_date,
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
        persisted = Listing(source=source, external_id=listing.source_external_id, **values)
    else:
        persisted = existing
        for field, value in values.items():
            setattr(persisted, field, value)
    persisted.full_clean(validate_unique=False, validate_constraints=False)
    if created:
        persisted.save()
    else:
        persisted.save(update_fields=[*values, "last_seen_at", "updated_at"])
    if source.can_retain_price_history and persisted.price is not None and (
        created or previous_price != persisted.price or not persisted.price_history.exists()
    ):
        ListingPriceHistory.objects.create(listing=persisted, price=persisted.price)
    match_listing_to_property(persisted)
    if run and persisted.external_id not in run.processed_ids:
        run.processed_ids.append(persisted.external_id)
        run.processed_count = len(run.processed_ids)
        run.save(update_fields=["processed_ids", "processed_count"])
    return persisted


def ingest_provider(source, provider: ListingProvider) -> list[Listing]:
    """Executa coleta, parsing, normalização e persistência fora do provider."""
    run = start_run(source)
    try:
        references = list(dict.fromkeys(provider.discover()))
        record_discovery(source, run.pk, references, provider.is_complete_snapshot)
        persisted = []
        for reference in references:
            raw_listing = provider.parse(provider.fetch(reference))
            normalized_listing = normalize_listing(raw_listing)
            listing = persist_listing(source, normalized_listing, run_id=run.pk)
            if listing:
                persisted.append(listing)
        reconcile_source_listings(source, [listing.external_id for listing in persisted], run_id=run.pk)
        return persisted
    except Exception as error:
        fail_run(run.pk, error)
        raise


@transaction.atomic
def reconcile_source_listings(source, seen_external_ids: list[str], *, run_id=None) -> int:
    """Desativa anúncios ativos que não apareceram nesta sincronização."""
    source = Source.objects.select_for_update().get(pk=source.pk)
    run = current_run(source, run_id) if run_id else None
    if run_id:
        if not run or run.status != "running" or not source.is_active:
            return 0
        if run.processed_count != run.expected_count or set(seen_external_ids) != set(run.processed_ids):
            raise ValueError("Sincronização não processou todas as referências.")
        run.status = "succeeded" if run.is_complete else "partial"
        run.finished_at = timezone.now()
        run.save(update_fields=["status", "finished_at"])
        if not run.is_complete:
            return 0
    queryset = Listing.objects.filter(source=source, is_active=True)
    if seen_external_ids:
        queryset = queryset.exclude(external_id__in=seen_external_ids)
    property_ids = list(queryset.exclude(property_id=None).values_list("property_id", flat=True).distinct())
    count = queryset.update(is_active=False)
    for property_id in sorted(set(property_ids)):
        refresh_property(property_id)
    if run:
        run.deactivated_count = count
        run.save(update_fields=["deactivated_count"])
    return count
