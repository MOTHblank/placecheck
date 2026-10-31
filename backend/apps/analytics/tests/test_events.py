from uuid import uuid4
from datetime import timedelta, timezone as utc_timezone
from io import StringIO
import json
from unittest.mock import patch

import pytest
from rest_framework.test import APIClient
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings
from django.utils import timezone
from django.db import connection
from django.db import close_old_connections
from concurrent.futures import ThreadPoolExecutor

from apps.listings.tests.factories import ListingFactory
from apps.analytics.models import MeasurementWindow
from apps.sources.tests.factories import SourceFactory


@pytest.fixture(autouse=True)
def public_traffic_policy(settings):
    settings.ANALYTICS_EXCLUDE_ALL = False


def command_report(*args):
    output = StringIO()
    call_command("journey_report", *args, stdout=output)
    return json.loads(output.getvalue())


def open_view(client, listing, **params):
    document = client.get(f"/api/properties/{listing.property_id}/", params).json()
    event = {"event_id": str(uuid4()), "kind": "view", "receipt": document["analytics_receipt"]}
    result = client.post("/api/analytics/events/", event, format="json")
    assert result.status_code == 201, result.data
    return result.json()["context_token"]


def expose(client, context, listing):
    event = {"event_id": str(uuid4()), "kind": "exposure", "context": context, "listing_id": listing.pk}
    result = client.post("/api/analytics/events/", event, format="json")
    assert result.status_code == 201, result.data
    return event, result.json()["redirect_token"]


@pytest.mark.django_db
def test_search_delivery_is_idempotent_and_conflicting_identity_is_rejected():
    client = APIClient()
    ListingFactory.create()
    receipt = client.get("/api/properties/").json()["analytics_receipt"]
    event_id = str(uuid4())
    event = {"event_id": event_id, "kind": "search", "receipt": receipt}
    first = client.post("/api/analytics/events/", event, format="json")
    assert first.status_code == 201
    assert first.json()["event_id"] == event_id
    repeated = client.post("/api/analytics/events/", event, format="json")
    assert repeated.status_code == 200
    assert repeated.json()["event_id"] == event_id
    changed_receipt = client.get("/api/properties/", {"bedrooms": 4}).json()["analytics_receipt"]
    conflicting = client.post("/api/analytics/events/", event | {"receipt": changed_receipt}, format="json")
    assert conflicting.status_code == 409
    assert command_report()["searches"] == 1


@pytest.mark.django_db
def test_two_exposures_and_repeated_clicks_produce_fifty_percent_ctr():
    client = APIClient()
    first = ListingFactory.create()
    second = ListingFactory.create(source=first.source, property=first.property, external_id="second")
    context = open_view(client, first, transaction_type="sale")
    event, token = expose(client, context, first)
    expose(client, context, second)
    assert client.post("/api/analytics/events/", event, format="json").status_code == 200
    for _ in range(3):
        assert client.get(f"/out/{first.pk}/", {"exposure": token}).status_code == 302
    row = command_report("--source", str(first.source_id))["sources"][0]
    assert (row["exposures"], row["exposures_with_redirect"], row["raw_redirects"]) == (2, 1, 3)
    assert row["ctr_percent"] == 50.0
    assert command_report("--source", str(first.source_id))["views"] is None


@pytest.mark.django_db
def test_another_event_identity_cannot_repeat_the_same_offer_in_one_opening():
    client = APIClient()
    listing = ListingFactory.create()
    context = open_view(client, listing)
    event, _ = expose(client, context, listing)
    repeated = client.post("/api/analytics/events/", event | {"event_id": str(uuid4())}, format="json")
    assert repeated.status_code == 409
    assert command_report("--source", str(listing.source_id))["sources"][0]["exposures"] == 1


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("same_identity", [False, True])
def test_simultaneous_identities_for_one_exposure_cannot_inflate_the_denominator(same_identity):
    listing = ListingFactory.create()
    context = open_view(APIClient(), listing)
    identity = str(uuid4())
    def send():
        close_old_connections()
        try:
            return APIClient().post("/api/analytics/events/", {"kind": "exposure", "event_id": identity if same_identity else str(uuid4()),
                "context": context, "listing_id": listing.pk}, format="json").status_code
        finally:
            close_old_connections()
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(send) for _ in range(2)]
        statuses = sorted(future.result(timeout=15) for future in futures)
    assert statuses == ([200, 201] if same_identity else [201, 409])
    assert command_report("--source", str(listing.source_id))["sources"][0]["exposures"] == 1


@pytest.mark.django_db
def test_exposure_revalidates_offer_after_waiting_for_source_lock():
    client = APIClient()
    listing = ListingFactory.create()
    context = open_view(client, listing)
    inactivated = False
    def another_ingestion_finishes_before_lock(execute, sql, params, many, context):
        nonlocal inactivated
        if not inactivated and '"sources_source"' in sql and "FOR UPDATE" in sql:
            inactivated = True
            # Storage-boundary interleaving: a reconciler finishes while this request waits.
            type(listing).objects.filter(pk=listing.pk).update(is_active=False)
        return execute(sql, params, many, context)
    with connection.execute_wrapper(another_ingestion_finishes_before_lock):
        response = client.post("/api/analytics/events/", {"kind": "exposure", "event_id": str(uuid4()),
            "context": context, "listing_id": listing.pk}, format="json")
    assert inactivated
    assert response.status_code == 202
    assert command_report()["sources"] == []


@pytest.mark.django_db
@pytest.mark.parametrize("seconds,attributed", [(0, 1), (1799, 1), (1800, 0), (1801, 0)])
def test_attribution_window_is_half_open(seconds, attributed):
    client, moment = APIClient(), timezone.now()
    listing = ListingFactory.create()
    with patch("django.utils.timezone.now", return_value=moment):
        context = open_view(client, listing)
        _, token = expose(client, context, listing)
    with patch("django.utils.timezone.now", return_value=moment + timedelta(seconds=seconds)):
        client.get(f"/out/{listing.pk}/", {"exposure": token})
        row = command_report("--source", str(listing.source_id), "--end",
                             (moment + timedelta(seconds=seconds + 1)).isoformat())["sources"][0]
    assert row["exposures_with_redirect"] == attributed
    assert row["raw_redirects"] == 1


@pytest.mark.django_db
def test_missing_bad_and_wrong_offer_attribution_only_increment_raw_redirects():
    client = APIClient()
    first, other = ListingFactory.create(), ListingFactory.create()
    _, token = expose(client, open_view(client, first), first)
    for params in ({}, {"exposure": "invalid"}, {"exposure": token}):
        assert client.get(f"/out/{other.pk}/", params).status_code == 302
    row = command_report("--source", str(other.source_id))["sources"][0]
    assert row["raw_redirects"] == 3
    assert row["attributed_redirects"] == 0
    assert row["ctr_percent"] is None


@pytest.mark.django_db
def test_property_or_demo_offer_not_returned_in_context_is_rejected():
    client = APIClient()
    listing = ListingFactory.create()
    other = ListingFactory.create()
    demo = ListingFactory.create(property=listing.property, source=SourceFactory.create(is_demo=True))
    context = open_view(client, listing)
    for invalid in (other, demo):
        response = client.post("/api/analytics/events/", {
            "event_id": str(uuid4()), "kind": "exposure", "context": context, "listing_id": invalid.pk,
        }, format="json")
        assert response.status_code == 400
    assert command_report()["sources"] == []


@pytest.mark.django_db
def test_withdrawal_and_listing_source_deletion_preserve_permitted_historical_counts():
    client = APIClient()
    listing = ListingFactory.create()
    key, name = listing.source_id, listing.source.name
    _, token = expose(client, open_view(client, listing), listing)
    client.get(f"/out/{listing.pk}/", {"exposure": token})
    source = listing.source
    source.is_published = False
    source.save()
    assert client.get(f"/out/{listing.pk}/").status_code == 404
    listing.delete()
    source.delete()
    row = command_report("--source", str(key))["sources"][0]
    assert row["source_name"] == name
    assert row["raw_redirects"] == 1 and row["ctr_percent"] == 100.0
    empty_market = command_report("--source", str(key), "--city", "Outra cidade", "--state", "BA", "--transaction", "sale")["sources"][0]
    assert empty_market["source_name"] == name
    assert empty_market["exposures"] == empty_market["raw_redirects"] == 0
    assert empty_market["ctr_percent"] is None
    empty_period = command_report("--source", str(key), "--start", timezone.now().isoformat())["sources"][0]
    assert empty_period["source_name"] == name and empty_period["ctr_percent"] is None


@pytest.mark.django_db
def test_analytics_retention_revocation_removes_source_events_and_stops_collection():
    client = APIClient()
    listing = ListingFactory.create()
    context = open_view(client, listing)
    _, token = expose(client, context, listing)
    client.get(f"/out/{listing.pk}/", {"exposure": token})
    source = listing.source
    source.can_retain_analytics = False
    source.save()
    assert client.get(f"/out/{listing.pk}/").status_code == 302
    result = client.post("/api/analytics/events/", {"event_id": str(uuid4()), "kind": "exposure",
                         "context": context, "listing_id": listing.pk}, format="json")
    assert result.status_code == 202
    row = command_report("--source", str(source.pk))["sources"][0]
    assert row["exposures"] == row["raw_redirects"] == 0


@pytest.mark.django_db
@pytest.mark.parametrize("headers", [{"HTTP_USER_AGENT": "Googlebot"}, {"HTTP_USER_AGENT": "HeadlessChrome/123"},
                                     {"HTTP_ORIGIN": "https://foreign.invalid"}])
def test_excluded_traffic_cannot_create_events_even_with_a_valid_receipt(headers):
    listing = ListingFactory.create()
    client = APIClient()
    receipt = client.get("/api/properties/").json()["analytics_receipt"]
    result = client.post("/api/analytics/events/", {"kind": "search", "event_id": str(uuid4()), "receipt": receipt},
                         format="json", **headers)
    assert result.status_code == 202
    assert client.get(f"/out/{listing.pk}/", **headers).status_code == 302
    report = command_report()
    assert report["searches"] == 0 and report["sources"] == []


@pytest.mark.django_db
@override_settings(ANALYTICS_EXCLUDE_ALL=True)
def test_internal_environment_and_demo_are_excluded_without_disabling_product():
    client = APIClient()
    listing = ListingFactory.create()
    assert client.get("/api/properties/").json()["analytics_receipt"] is None
    assert client.get(f"/out/{listing.pk}/").status_code == 302
    assert command_report()["sources"] == []


@pytest.mark.django_db
def test_property_views_use_one_explicit_market_or_remain_unattributed():
    client = APIClient()
    listing = ListingFactory.create(city="Salvador", state="BA")
    # Property's location is the view context; fixture factory locations must match.
    listing.property.city, listing.property.state = "Salvador", "BA"
    listing.property.save()
    open_view(client, listing, transaction_type="sale")
    open_view(client, listing)
    report = command_report("--city", "Salvador", "--state", "BA", "--transaction", "sale")
    assert report["views"] == 1 and report["unattributed_views"] == 1
    assert command_report()["views"] == 2


@pytest.mark.django_db
def test_cleanup_removes_expired_events_and_refuses_reporting_expired_periods():
    client = APIClient()
    listing = ListingFactory.create()
    old = timezone.now()
    context = open_view(client, listing)
    _, token = expose(client, context, listing)
    client.get(f"/out/{listing.pk}/", {"exposure": token})
    with patch("django.utils.timezone.now", return_value=old + timedelta(days=90, minutes=1)):
        output = StringIO()
        call_command("purge_analytics", stdout=output)
        result = json.loads(output.getvalue())
        assert result["events_deleted"] == 2 and result["redirects_deleted"] == 1
        report = command_report()
        assert report["views"] == 0 and report["sources"] == []
        with pytest.raises(CommandError, match="disponíveis"):
            command_report("--start", old.isoformat())


@pytest.mark.django_db
@pytest.mark.parametrize("args", [
    ("--timezone", "Bad/Zone"), ("--source", "999999"), ("--city", "Salvador"),
    ("--timezone", "America/New_York", "--start", "2026-11-01T01:30:00"),
    ("--timezone", "America/New_York", "--start", "2026-03-08T02:30:00"),
])
def test_report_rejects_unknown_filters_and_ambiguous_or_nonexistent_local_times(args):
    with pytest.raises(CommandError):
        command_report(*args)


@pytest.mark.django_db
def test_ctr_uses_exposure_day_while_raw_redirect_uses_click_day():
    client = APIClient()
    # Fixed local example within the test's available history.
    today = timezone.now().astimezone(utc_timezone.utc).replace(hour=3, minute=0, second=0, microsecond=0)
    seen_at, clicked_at = today - timedelta(minutes=5), today + timedelta(minutes=5)
    window = MeasurementWindow.objects.get(pk=1)
    window.started_at = today - timedelta(days=2)
    window.save()
    listing = ListingFactory.create()
    with patch("django.utils.timezone.now", return_value=seen_at):
        _, token = expose(client, open_view(client, listing), listing)
    with patch("django.utils.timezone.now", return_value=clicked_at):
        client.get(f"/out/{listing.pk}/", {"exposure": token})
    with patch("django.utils.timezone.now", return_value=clicked_at + timedelta(seconds=1)):
        yesterday = command_report("--source", str(listing.source_id), "--start", (today - timedelta(days=1)).isoformat(), "--end", today.isoformat())
        current = command_report("--source", str(listing.source_id), "--start", today.isoformat())
    assert yesterday["sources"][0]["ctr_percent"] == 100.0
    assert yesterday["sources"][0]["raw_redirects"] == 0
    assert current["sources"][0]["ctr_percent"] is None
    assert current["sources"][0]["raw_redirects"] == 1


@pytest.mark.django_db
def test_cleanup_includes_exact_ninety_day_boundary():
    client = APIClient()
    moment = timezone.now()
    listing = ListingFactory.create()
    with patch("django.utils.timezone.now", return_value=moment):
        _, token = expose(client, open_view(client, listing), listing)
        client.get(f"/out/{listing.pk}/", {"exposure": token})
    with patch("django.utils.timezone.now", return_value=moment + timedelta(days=90)):
        output = StringIO()
        call_command("purge_analytics", stdout=output)
    assert json.loads(output.getvalue())["events_deleted"] == 2
    assert json.loads(output.getvalue())["redirects_deleted"] == 1


@pytest.mark.django_db
def test_recent_redirect_classification_survives_expiration_of_its_older_exposure():
    client = APIClient()
    moment = timezone.now()
    listing = ListingFactory.create()
    with patch("django.utils.timezone.now", return_value=moment):
        _, token = expose(client, open_view(client, listing), listing)
    with patch("django.utils.timezone.now", return_value=moment + timedelta(minutes=20)):
        client.get(f"/out/{listing.pk}/", {"exposure": token})
    with patch("django.utils.timezone.now", return_value=moment + timedelta(days=90, seconds=1)):
        call_command("purge_analytics", stdout=StringIO())
        row = command_report("--source", str(listing.source_id))["sources"][0]
    assert row["exposures"] == 0 and row["ctr_percent"] is None
    assert row["raw_redirects"] == row["attributed_redirects"] == 1


@pytest.mark.django_db
def test_staff_and_demo_are_excluded_and_reports_have_no_public_endpoint():
    from django.contrib.auth import get_user_model
    client = APIClient()
    listing = ListingFactory.create(source=SourceFactory.create(is_demo=True))
    assert client.get(f"/api/properties/{listing.property_id}/").json()["analytics_receipt"] is None
    assert client.get(f"/out/{listing.pk}/").status_code == 302
    assert command_report()["sources"] == []
    real = ListingFactory.create()
    client.force_authenticate(get_user_model().objects.create(username="staff", is_staff=True))
    assert client.get(f"/api/properties/{real.property_id}/").json()["analytics_receipt"] is None
    assert client.post("/api/analytics/events/", {"kind": "search", "event_id": str(uuid4())}, format="json").status_code == 202
    assert client.get(f"/out/{real.pk}/").status_code == 302
    assert command_report()["sources"] == []
    assert client.get("/api/analytics/report/").status_code == 404


@pytest.mark.parametrize("url", ["/out/1/?exposure=private-token", "/api/properties/?q=private-token"])
def test_access_logging_does_not_retain_attribution_tokens_or_search_text(url):
    import logging
    from apps.analytics.logging import RedactAttribution
    record = logging.LogRecord("django.server", logging.INFO, "", 1, '"GET %s HTTP/1.1" 302', (url,), None)
    RedactAttribution().filter(record)
    assert "private-token" not in record.getMessage()
    assert url.split("?")[0] in record.getMessage()
