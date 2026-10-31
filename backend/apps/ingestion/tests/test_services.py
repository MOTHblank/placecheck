import pytest
from decimal import Decimal

from apps.ingestion.services import ingest_provider
from apps.listings.models import Listing, ListingPriceHistory
from apps.sources.providers import ManualProvider
from apps.sources.tests.factories import SourceFactory
from apps.sources.tests.test_provider import sample_record


@pytest.mark.django_db
def test_provider_pipeline_persists_normalized_listings():
    source = SourceFactory.create()
    provider = ManualProvider({"manual-001": sample_record()})

    persisted = ingest_provider(source, provider)

    listing = Listing.objects.get(source=source, external_id="manual-001")
    assert persisted == [listing]
    assert listing.price == Decimal("650000.00")
    assert listing.area == Decimal("80.50")
    assert listing.bedrooms == 3
    assert listing.transaction_type == Listing.TransactionType.SALE


@pytest.mark.django_db
def test_provider_pipeline_updates_existing_listing():
    source = SourceFactory.create()
    provider = ManualProvider({"manual-001": sample_record()})
    first = ingest_provider(source, provider)[0]

    changed = sample_record()
    changed["price"] = "R$ 640.000,00"
    ingest_provider(source, ManualProvider({"manual-001": changed}))

    assert Listing.objects.get(pk=first.pk).price == Decimal("640000.00")
    assert Listing.objects.filter(source=source, external_id="manual-001").count() == 1


@pytest.mark.django_db
def test_price_history_is_idempotent_and_records_changes():
    source = SourceFactory.create()
    provider = ManualProvider({"manual-001": sample_record()})

    ingest_provider(source, provider)
    ingest_provider(source, provider)
    changed = sample_record()
    changed["price"] = "R$ 640.000,00"
    ingest_provider(source, ManualProvider({"manual-001": changed}))

    prices = list(
        ListingPriceHistory.objects.filter(listing__source=source)
        .order_by("captured_at")
        .values_list("price", flat=True)
    )
    assert prices == [Decimal("650000.00"), Decimal("640000.00")]


@pytest.mark.django_db
def test_missing_listings_are_deactivated_during_reconciliation():
    source = SourceFactory.create()
    first = sample_record("manual-001")
    second = sample_record("manual-002")
    ingest_provider(source, ManualProvider({"manual-001": first, "manual-002": second}))

    ingest_provider(source, ManualProvider({"manual-001": first}))

    assert Listing.objects.get(source=source, external_id="manual-001").is_active is True
    assert Listing.objects.get(source=source, external_id="manual-002").is_active is False
