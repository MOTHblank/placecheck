import pytest
from decimal import Decimal
from dataclasses import replace
from unittest.mock import patch

from apps.ingestion.services import ingest_provider
from apps.ingestion.services import persist_listing, reconcile_source_listings
from apps.sources.normalizers import normalize_listing
from apps.listings.models import Listing, ListingPriceHistory
from apps.properties.models import Property
from apps.sources.providers import ManualProvider
from apps.sources.tests.factories import SourceFactory
from apps.sources.tests.test_provider import sample_record


@pytest.mark.django_db
@pytest.mark.parametrize("field,value", [("source_external_id", ""), ("title", ""), ("url", "javascript:alert(1)"), ("transaction_type", "invalid"), ("city", ""), ("state", "")])
def test_persistence_rejects_invalid_required_fields_without_partial_writes(field, value):
    from django.core.exceptions import ValidationError

    source = SourceFactory.create()
    normalized = normalize_listing(ManualProvider({}).parse(sample_record()))
    with pytest.raises(ValidationError):
        persist_listing(source, replace(normalized, **{field: value}))
    assert not Listing.objects.exists()
    assert not ListingPriceHistory.objects.exists()


@pytest.mark.django_db
def test_plan_prices_reach_comparison_with_idempotent_history_and_reactivation():
    from rest_framework.test import APIClient

    source = SourceFactory.create()
    record = sample_record()
    record["price"] = "R$ 650.000"
    first = ingest_provider(source, ManualProvider({"manual-001": record}))[0]
    first_seen = first.first_seen_at
    last_seen = first.last_seen_at
    ingest_provider(source, ManualProvider({"manual-001": record}))
    reconcile_source_listings(source, [])
    record["price"] = "R$ 640.000"
    updated = ingest_provider(source, ManualProvider({"manual-001": record}))[0]
    assert updated.pk == first.pk
    assert updated.is_active
    assert updated.first_seen_at == first_seen
    assert updated.last_seen_at > last_seen
    response = APIClient().get(f"/api/properties/{updated.property_id}/")
    assert response.status_code == 200
    offer = response.data["listings"][0]
    assert offer["price"] == "640000.00"
    assert offer["previous_price"] == "650000.00"
    assert [entry["price"] for entry in offer["price_history"]] == ["640000.00", "650000.00"]


@pytest.mark.django_db
def test_description_is_not_stored_without_source_permission():
    source = SourceFactory.create(can_store_description=False)
    listing = ingest_provider(source, ManualProvider({"manual-001": sample_record()}))[0]
    assert listing.description == ""


@pytest.mark.django_db(transaction=True)
def test_persistence_owns_its_transaction_outside_synchronous_ingestion():
    source = SourceFactory.create()
    normalized = normalize_listing(ManualProvider({}).parse(sample_record()))
    first = persist_listing(source, normalized)
    second = persist_listing(source, normalized)
    assert first.pk == second.pk
    assert first.price_history.count() == 1


@pytest.mark.django_db(transaction=True)
def test_failed_matching_rolls_back_listing_and_price_history_together():
    source = SourceFactory.create()
    normalized = normalize_listing(ManualProvider({}).parse(sample_record()))
    listing = persist_listing(source, normalized)
    last_seen = listing.last_seen_at
    property_id = listing.property_id
    with patch("apps.ingestion.services.match_listing_to_property", side_effect=RuntimeError("matching failed")):
        with pytest.raises(RuntimeError):
            persist_listing(source, replace(normalized, price=Decimal("500000")))
    listing.refresh_from_db()
    assert listing.price == Decimal("650000")
    assert listing.price_history.count() == 1
    assert listing.last_seen_at == last_seen
    assert listing.property_id == property_id


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


@pytest.mark.django_db
def test_unchanged_listing_keeps_property_when_other_offer_becomes_inactive():
    first_source = SourceFactory.create()
    second_source = SourceFactory.create()
    record = sample_record()
    record["title"] = "Apartamento em Pinheiros unidade 401"
    normalized = normalize_listing(ManualProvider({}).parse(record))
    first = persist_listing(first_source, normalized)
    second = persist_listing(second_source, normalized)
    original_property_id = first.property_id
    assert second.property_id == original_property_id

    reconcile_source_listings(second_source, [])
    for _ in range(2):
        unchanged = persist_listing(first_source, normalized)
        assert unchanged.property_id == original_property_id

    assert Property.objects.count() == 1
    assert unchanged.price_history.count() == 1
    assert unchanged.match_decisions.latest("id").assigned_property_id == original_property_id
    reactivated = persist_listing(second_source, normalized)
    assert reactivated.is_active
    assert reactivated.property_id == original_property_id
    assert Property.objects.count() == 1
