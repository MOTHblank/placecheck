import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from apps.ingestion.services import ingest_provider
from apps.sources.providers import ManualProvider
from apps.sources.providers.registry import build_provider
from apps.sources.tests.factories import SourceFactory
from apps.sources.tests.test_provider import sample_record


@pytest.mark.django_db
@override_settings(MANUAL_PROVIDER_RECORDS={})
def test_missing_configuration_is_not_an_empty_inventory():
    source = SourceFactory.create()
    with pytest.raises(ImproperlyConfigured):
        build_provider(source)


@pytest.mark.django_db
def test_partial_inventory_preserves_absent_offers_and_confirmed_empty_removes_them():
    source = SourceFactory.create()
    listing = ingest_provider(source, ManualProvider({"manual-001": sample_record()}))[0]
    ingest_provider(source, ManualProvider({}, complete=False))
    listing.refresh_from_db()
    assert listing.is_active
    assert source.sync_runs.latest("id").status == "partial"
    ingest_provider(source, ManualProvider({}))
    listing.refresh_from_db()
    assert not listing.is_active
    run = source.sync_runs.latest("id")
    assert run.status == "succeeded"
    assert run.is_complete
    assert run.deactivated_count == 1


@pytest.mark.django_db(transaction=True)
def test_old_run_cannot_write_or_reconcile_after_new_run_starts():
    from dataclasses import replace
    from decimal import Decimal
    from apps.ingestion.runs import record_discovery, start_run
    from apps.ingestion.services import persist_listing, reconcile_source_listings
    from apps.sources.normalizers import normalize_listing

    source = SourceFactory.create()
    normalized = normalize_listing(ManualProvider({}).parse(sample_record()))
    old = start_run(source)
    record_discovery(source, old.pk, ["manual-001"], True)
    persist_listing(source, normalized, run_id=old.pk)
    new = start_run(source)
    record_discovery(source, new.pk, ["manual-001"], True)
    updated = persist_listing(source, replace(normalized, price=Decimal("600000")), run_id=new.pk)
    assert persist_listing(source, normalized, run_id=old.pk) is None
    assert reconcile_source_listings(source, [], run_id=old.pk) == 0
    reconcile_source_listings(source, ["manual-001"], run_id=new.pk)
    updated.refresh_from_db()
    assert updated.price == Decimal("600000")
    assert updated.is_active
    assert updated.price_history.count() == 2
    old.refresh_from_db()
    assert old.status == "superseded"


@pytest.mark.django_db
def test_failed_partial_capture_keeps_absent_inventory_and_reports_failure():
    source = SourceFactory.create()
    listing = ingest_provider(source, ManualProvider({"manual-001": sample_record()}))[0]
    with pytest.raises(KeyError):
        ingest_provider(source, ManualProvider({"bad": {}}))
    listing.refresh_from_db()
    assert listing.is_active
    run = source.sync_runs.latest("id")
    assert run.status == "failed"
    assert run.failure == "KeyError"
