from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from decimal import Decimal
from threading import Barrier, Event
from time import monotonic
from unittest.mock import patch

import pytest
from django.db import close_old_connections, connection

from apps.deduplication import services as matching
from apps.ingestion.services import persist_listing
from apps.sources.normalizers import normalize_listing
from apps.sources.providers import ManualProvider
from apps.sources.tests.factories import SourceFactory
from apps.sources.tests.test_provider import sample_record


def wait_for_block_or_completion(future, backend_pid):
    """Wait for an actual PostgreSQL lock, rather than guess worker timing."""
    deadline = monotonic() + 10
    while not future.done():
        with connection.cursor() as cursor:
            cursor.execute("SELECT cardinality(pg_blocking_pids(%s))", [backend_pid])
            if cursor.fetchone()[0]:
                return
        if monotonic() >= deadline:
            pytest.fail("Concurrent ingestion neither completed nor waited for a lock")
        Event().wait(0.01)


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("second_area, should_share", [("98", True), ("102", False)])
def test_concurrent_join_rechecks_all_group_members(second_area, should_share):
    sources = [SourceFactory.create() for _ in range(3)]
    record = sample_record()
    record["title"] = "Apartamento em Pinheiros unidade 401"
    normalized = normalize_listing(ManualProvider({}).parse(record))
    anchor = persist_listing(sources[0], replace(normalized, area=Decimal("100")))
    first_paused = Event()
    release_first = Event()
    second_connected = Event()
    second_pid = []
    real_refresh = matching.refresh_property

    def pause_first_join(property_id):
        if not first_paused.is_set():
            first_paused.set()
            assert release_first.wait(10), "First ingestion was never released"
        return real_refresh(property_id)

    def ingest(index, area):
        close_old_connections()
        try:
            if index == 2:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT pg_backend_pid()")
                    second_pid.append(cursor.fetchone()[0])
                second_connected.set()
            return persist_listing(sources[index], replace(normalized, area=Decimal(area)))
        finally:
            connection.close()

    with patch.object(matching, "refresh_property", pause_first_join):
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(ingest, 1, "98")
            try:
                assert first_paused.wait(10), "First ingestion did not reach group assignment"
                second = pool.submit(ingest, 2, second_area)
                assert second_connected.wait(10), "Second ingestion did not connect"
                wait_for_block_or_completion(second, second_pid[0])
            finally:
                release_first.set()
            first_offer = first.result(timeout=10)
            second_offer = second.result(timeout=10)

    assert first_offer.property_id == anchor.property_id
    assert matching.calculate_similarity(first_offer, second_offer).automatic is should_share
    assert (second_offer.property_id == first_offer.property_id) is should_share


@pytest.mark.django_db(transaction=True)
def test_concurrent_updates_of_group_members_do_not_deadlock():
    sources = [SourceFactory.create() for _ in range(2)]
    record = sample_record()
    record["title"] = "Apartamento em Pinheiros unidade 401"
    normalized = normalize_listing(ManualProvider({}).parse(record))
    original = [persist_listing(source, normalized) for source in sources]
    assert original[0].property_id == original[1].property_id
    updates_ready = Barrier(2)

    def synchronize_updates(listing):
        updates_ready.wait(timeout=10)
        return matching.match_listing_to_property(listing)

    def update(source):
        close_old_connections()
        try:
            return persist_listing(source, replace(normalized, price=Decimal("640000")))
        finally:
            connection.close()

    with patch("apps.ingestion.services.match_listing_to_property", synchronize_updates):
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(update, source) for source in sources]
            updated = [future.result(timeout=10) for future in futures]

    assert all(listing.property_id == original[0].property_id for listing in updated)
    assert all(listing.price_history.count() == 2 for listing in updated)
