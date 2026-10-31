from io import StringIO
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection, close_old_connections, transaction

from apps.ingestion.services import ingest_provider
from apps.sources.providers import ManualProvider
from apps.sources.tests.test_provider import sample_record

from apps.listings.models import ListingPriceHistory
from apps.listings.tests.factories import ListingFactory
from apps.properties.tests.factories import PropertyFactory
from apps.sources.tests.factories import SourceFactory

pytestmark = pytest.mark.django_db(transaction=True)


def report(*args):
    output = StringIO()
    call_command("inventory_report", *args, stdout=output)
    return json.loads(output.getvalue())


def test_inventory_counts_current_public_stock_and_retained_history():
    first = SourceFactory.create(is_active=False)
    second = SourceFactory.create()
    SourceFactory.create()  # A published Source with no offers still counts without a market filter.
    properties = [PropertyFactory.create() for _ in range(4)]
    assignments = [(first, 0), (second, 0), (first, 1), (second, 1), (first, 2), (second, 3)]
    listings = [ListingFactory.create(source=source, property=properties[group], external_id=f"stock-{index}")
                for index, (source, group) in enumerate(assignments)]
    inactive = ListingFactory.create(source=first, external_id="inactive", is_active=False)
    for listing in (listings[0], listings[0], inactive):
        ListingPriceHistory.objects.create(listing=listing, price=600000)
    PropertyFactory.create()  # Unrepresented Properties do not enter the denominator.
    for source in (SourceFactory.create(is_demo=True), SourceFactory.create(is_published=False)):
        listing = ListingFactory.create(source=source)
        ListingPriceHistory.objects.create(listing=listing, price=500000)
    result = report()
    assert result["snapshot_kind"] == "current"
    assert result["stock"] == {"publishable_sources": 3, "active_listings": 6, "represented_properties": 4,
                               "properties_with_multiple_offers": 2, "retained_price_histories": 3,
                               "unassigned_active_listings": 0}
    assert result["grouping_reduction_percent"] == 33.333333


def test_source_and_market_filters_apply_to_one_population_and_ignore_property_projection():
    first, second = SourceFactory.create(), SourceFactory.create()
    property_ = PropertyFactory.create(city="Cidade projetada", state="SP")
    sale = ListingFactory.create(source=first, property=property_, city="Salvador", state="BA")
    rent = ListingFactory.create(source=second, property=property_, city="Salvador", state="BA", transaction_type="rent")
    ListingFactory.create(source=first, property=property_, external_id="other-city", city="São Paulo", state="SP")
    for listing in (sale, rent):
        ListingPriceHistory.objects.create(listing=listing, price=100000)
    result = report("--city", "salvador", "--state", "ba", "--transaction", "sale")
    assert result["stock"]["publishable_sources"] == result["stock"]["active_listings"] == 1
    assert result["stock"]["represented_properties"] == result["stock"]["retained_price_histories"] == 1
    assert result["stock"]["properties_with_multiple_offers"] == 0
    assert result["grouping_reduction_percent"] == 0.0
    assert [row["source_id"] for row in result["sources"]] == [first.pk]
    own = report("--source", str(second.pk))
    assert own["stock"]["active_listings"] == 1
    empty = report("--source", str(second.pk), "--city", "Salvador", "--state", "BA", "--transaction", "sale")
    assert empty["stock"]["active_listings"] == empty["stock"]["publishable_sources"] == 0
    assert empty["sources"][0]["source_id"] == second.pk
    assert empty["sources"][0]["synchronization_scope"] == "whole_source"


def test_pause_preserves_stock_withdrawal_excludes_it_and_history_permission_is_independent():
    source = SourceFactory.create(can_retain_analytics=False)
    listing = ListingFactory.create(source=source)
    ListingPriceHistory.objects.create(listing=listing, price=100000)
    source.is_active = False
    source.save()
    paused = report("--source", str(source.pk))
    assert paused["stock"]["active_listings"] == paused["stock"]["retained_price_histories"] == 1
    assert paused["sources"][0]["collection_paused"] is True
    source.can_retain_price_history = False
    source.save()
    # Even incorrectly retained data must not contribute when permission is denied.
    ListingPriceHistory.objects.create(listing=listing, price=50000)
    assert report()["stock"]["retained_price_histories"] == 0
    source.is_published = False
    source.save()
    withdrawn = report()
    assert withdrawn["stock"]["active_listings"] == withdrawn["stock"]["publishable_sources"] == 0
    assert withdrawn["sources"][0]["is_published"] is False
    assert withdrawn["grouping_reduction_percent"] is None


def test_empty_stock_and_unassigned_listings_have_explicit_unavailable_reasons():
    source = SourceFactory.create()
    empty = report()
    assert empty["stock"]["publishable_sources"] == 1
    assert empty["grouping_reduction_percent"] is None
    assert empty["grouping_reduction_unavailable_reason"] == "empty_stock"
    ListingFactory.create(source=source, property=None)
    inconsistent = report()
    assert inconsistent["stock"]["active_listings"] == inconsistent["stock"]["unassigned_active_listings"] == 1
    assert inconsistent["stock"]["represented_properties"] == 0
    assert inconsistent["grouping_reduction_percent"] is None
    assert inconsistent["grouping_reduction_unavailable_reason"] == "unassigned_listings"


def test_ingestion_partial_failure_and_complete_empty_have_distinct_observable_status():
    source = SourceFactory.create()
    ingest_provider(source, ManualProvider({"one": sample_record()}))
    complete = report()["sources"][0]["latest_complete_success"]
    assert complete["status"] == "succeeded" and complete["is_complete"] is True
    assert complete["processed_count"] == 1 and complete["deactivated_count"] == 0
    ingest_provider(source, ManualProvider({}, complete=False))
    partial = report()
    assert partial["stock"]["active_listings"] == 1
    assert partial["sources"][0]["latest_complete_success"]["id"] == complete["id"]
    assert partial["sources"][0]["latest_run"]["status"] == "partial"
    invalid = sample_record() | {"price": "invalid"}
    with pytest.raises(ValueError):
        ingest_provider(source, ManualProvider({"one": invalid}))
    failed = report()["sources"][0]
    assert failed["latest_failure"]["failure_type"] == "ValueError"
    assert failed["latest_failure"]["finished_at"] is not None
    assert failed["latest_complete_success"]["id"] == complete["id"]
    ingest_provider(source, ManualProvider({}))
    current = report()
    assert current["stock"]["active_listings"] == 0
    assert current["stock"]["retained_price_histories"] == 1
    assert current["sources"][0]["latest_complete_success"]["deactivated_count"] == 1
    assert current["sources"][0]["latest_complete_success"]["processed_count"] == 0
    assert current["sources"][0]["latest_failure"]["id"] == failed["latest_failure"]["id"]
    assert report("--city", "São Paulo", "--state", "SP", "--transaction", "sale")["sources"][0]["latest_complete_success"]["deactivated_count"] == 1


def test_reingestion_changes_grouping_without_rewriting_a_stock_history():
    first, second = SourceFactory.create(), SourceFactory.create()
    record = sample_record() | {"title": "Apartamento Pinheiros unidade 101", "source_external_id": "one"}
    ingest_provider(first, ManualProvider({"one": record}))
    ingest_provider(second, ManualProvider({"one": record}))
    grouped = report()
    assert grouped["stock"]["active_listings"] == 2 and grouped["stock"]["represented_properties"] == 1
    assert grouped["grouping_reduction_percent"] == 50.0
    ingest_provider(second, ManualProvider({"one": record | {"title": "Apartamento Pinheiros unidade 202"}}))
    separated = report()
    assert separated["stock"]["active_listings"] == separated["stock"]["represented_properties"] == 2
    assert separated["stock"]["properties_with_multiple_offers"] == 0
    assert separated["grouping_reduction_percent"] == 0.0
    assert separated["snapshot_kind"] == "current"


def test_snapshot_is_consistent_while_ingestion_updates_inventory_and_runs():
    listing = ListingFactory.create()
    changed = False
    def reconcile():
        close_old_connections()
        try:
            ingest_provider(type(listing.source).objects.get(pk=listing.source_id), ManualProvider({}))
        finally:
            close_old_connections()
    def interleave(execute, sql, params, many, context):
        nonlocal changed
        result = execute(sql, params, many, context)
        if not changed and 'FROM "sources_source"' in sql:
            changed = True
            with ThreadPoolExecutor(max_workers=1) as pool:
                pool.submit(reconcile).result(timeout=15)
        return result
    with connection.execute_wrapper(interleave):
        frozen = report()
    assert changed
    assert frozen["stock"]["active_listings"] == 1
    assert frozen["sources"][0]["latest_complete_success"] is None
    current = report()
    assert current["stock"]["active_listings"] == 0
    assert current["sources"][0]["latest_complete_success"]["deactivated_count"] == 1


@pytest.mark.parametrize("args", [("--source", "99999"), ("--source", "-1"), ("--city", "Salvador"),
    ("--timezone", "Unknown/Zone"), ("--start", "2026-10-01"), ("--end", "2026-10-31")])
def test_invalid_filters_and_historical_stock_requests_are_rejected(args):
    with pytest.raises(CommandError):
        report(*args)


def test_timezone_and_demo_selection_and_transaction_boundary_are_explicit():
    source = SourceFactory.create(is_demo=True)
    ListingFactory.create(source=source)
    result = report("--source", str(source.pk), "--timezone", "UTC")
    assert result["sources"] == [] and result["stock"]["publishable_sources"] == 0
    assert datetime.fromisoformat(result["snapshot_at"]).utcoffset().total_seconds() == 0
    with transaction.atomic():
        with pytest.raises(CommandError, match="transação"):
            report()
