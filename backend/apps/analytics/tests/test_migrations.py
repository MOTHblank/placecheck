from datetime import timedelta
from io import StringIO
import json
from uuid import uuid4

import pytest
from django.core.management import call_command
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.utils import timezone

from apps.analytics.models import JourneyEvent, MeasurementWindow, RedirectEvent
from apps.listings.tests.factories import ListingFactory


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("click_offsets,attributed", [([11], 1), ([30, 41], 0), ([11, 30, 41], 1)])
def test_legacy_duplicate_upgrade_keeps_only_clicks_in_original_exposure_window(click_offsets, attributed):
    latest = MigrationExecutor(connection).loader.graph.leaf_nodes()
    MigrationExecutor(connection).migrate([("analytics", "0004_redirectevent_was_attributed")])
    try:
        moment = timezone.now() - timedelta(hours=2)
        window, _ = MeasurementWindow.objects.get_or_create(pk=1)
        window.started_at = moment - timedelta(minutes=1)
        window.save()
        listing = ListingFactory.create()
        context = uuid4()
        exposures = []
        for minutes in (0, 10, 40):
            exposures.append(JourneyEvent.objects.create(
                kind="exposure", context_id=context, listing_key=listing.pk, property_key=listing.property_id,
                source_key=listing.source_id, source_slug=listing.source.slug, source_name=listing.source.name,
                city=listing.city, state=listing.state, transaction_type="sale", payload_digest="0" * 64,
                created_at=moment + timedelta(minutes=minutes)))
        for minutes in click_offsets:
            RedirectEvent.objects.create(listing=listing, listing_key=listing.pk,
                source_key=listing.source_id, source_slug=listing.source.slug, source_name=listing.source.name,
                city=listing.city, state=listing.state, transaction_type="sale", was_attributed=True,
                exposure=exposures[1 if minutes <= 30 else 2], created_at=moment + timedelta(minutes=minutes))
        MigrationExecutor(connection).migrate(latest)
        output = StringIO()
        call_command("journey_report", "--source", str(listing.source_id), stdout=output)
        row = json.loads(output.getvalue())["sources"][0]
        assert row["exposures"] == 1
        assert row["raw_redirects"] == len(click_offsets)
        assert row["attributed_redirects"] == attributed
        assert row["ctr_percent"] == (100.0 if attributed else 0.0)
    finally:
        MigrationExecutor(connection).migrate(latest)
