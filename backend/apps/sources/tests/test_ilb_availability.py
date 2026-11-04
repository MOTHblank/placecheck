from datetime import timedelta
from io import BytesIO
import json
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.error import URLError

import pytest
from django.core.cache import cache, caches
from django.core.management import call_command
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.listings.models import Listing
from apps.listings.tests.factories import ListingFactory
from apps.sources.models import Source
from apps.sources.providers.imoveis_leilao_brasil import SOURCE_SLUG
from apps.sources.providers.registry import build_provider
from apps.sources.normalizers import normalize_listing
from apps.ingestion.services import persist_listing
from apps.ingestion.availability import record_availability_check
from apps.ingestion.exceptions import SourceRateLimitExceeded
from apps.ingestion.limits import check_source_rate_limit
from .test_ilb_pipeline import PILOT_SETTINGS
from .test_ilb_provider import api_item


def old_listing():
    call_command("setup_ilb_pilot")
    source = Source.objects.get(slug=SOURCE_SLUG)
    listing = ListingFactory.create(source=source, external_id="1234567890123", city="Salvador", state="BA")
    Listing.objects.filter(pk=listing.pk).update(last_seen_at=timezone.now() - timedelta(days=2))
    listing.refresh_from_db()
    return listing


def missing_response():
    return HTTPError("https://www.imoveisleilaobrasil.com.br/api/imovel/1234567890123", 404,
                     "Not Found", {"Content-Type": "application/json; charset=utf-8"},
                     BytesIO(b'{"erro":"nao encontrado"}'))


@pytest.mark.django_db
@override_settings(**PILOT_SETTINGS)
def test_confirmed_detail_absence_removes_only_that_offer_from_public_journey():
    from apps.sources.tasks import check_ilb_listing_availability

    cache.clear()
    listing = old_listing()
    other = ListingFactory.create(source=listing.source, external_id="9876543210123")
    before = listing.last_seen_at
    with patch("urllib.request.OpenerDirector.open", side_effect=missing_response()):
        result = check_ilb_listing_availability.delay(listing.source_id, listing.pk)
    assert result.get() == "missing"
    client = APIClient()
    assert client.get(f"/out/{listing.pk}/").status_code == 404
    assert client.get(f"/api/properties/{listing.property_id}/").status_code == 404
    assert client.get(f"/out/{other.pk}/").status_code == 302
    listing.refresh_from_db()
    assert not listing.is_active and listing.last_seen_at == before
    assert listing.availability_check.status == "missing"


@pytest.mark.django_db
@override_settings(**PILOT_SETTINGS)
def test_scheduled_checks_ignore_recent_captures_and_do_not_repeat_success_within_a_day():
    from apps.sources.tasks import queue_ilb_availability_checks

    cache.clear()
    listing = old_listing()
    ListingFactory.create(source=listing.source, external_id="9876543210123")
    with patch("urllib.request.OpenerDirector.open", return_value=BytesIO(json.dumps(api_item()).encode())) as network:
        assert queue_ilb_availability_checks.delay().get() == 1
        assert queue_ilb_availability_checks.delay().get() == 0
    assert network.call_count == 1
    listing.refresh_from_db()
    assert listing.is_active and listing.availability_check.status == "available"


@pytest.mark.django_db
@override_settings(**PILOT_SETTINGS)
@pytest.mark.parametrize("code,content_type,body,calls", [
    (404, "text/html", b"<html>Not Found</html>", 1),
    (404, "text/html", b'{"erro":"nao encontrado"}', 1),
    (404, "application/json", b'{"erro":"bloqueado"}', 1),
    (404, "application/json", b"null", 1),
    (403, "application/json", b'{"erro":"nao encontrado"}', 1),
    (429, "application/json", b"{}", 4),
    (503, "application/json", b"{}", 4),
])
def test_http_failures_preserve_offers_and_record_unknown_availability(code, content_type, body, calls):
    from apps.sources.tasks import check_ilb_listing_availability

    cache.clear()
    listing = old_listing()
    before = listing.last_seen_at
    def rejected(*args, **kwargs):
        raise HTTPError("https://unused.invalid", code, "error", {"Content-Type": content_type}, BytesIO(body))
    with patch("urllib.request.OpenerDirector.open", side_effect=rejected) as network:
        assert check_ilb_listing_availability.delay(listing.source_id, listing.pk).get() == "failed"
    assert network.call_count == calls
    assert APIClient().get(f"/out/{listing.pk}/").status_code == 302
    listing.refresh_from_db()
    assert listing.is_active and listing.last_seen_at == before
    assert listing.availability_check.status == "failed"
    assert listing.availability_check.failure in ("ValueError", "ProviderTemporaryError")
    with patch("urllib.request.OpenerDirector.open", side_effect=AssertionError("Daily cooldown")):
        assert check_ilb_listing_availability.delay(listing.source_id, listing.pk).get() == "skipped"


@pytest.mark.django_db
@override_settings(**PILOT_SETTINGS)
@pytest.mark.parametrize("body", [b"null", b"[]", b"<html>blocked</html>", b"x" * 1_048_577,
    json.dumps(api_item(id="9999999999999")).encode(), json.dumps(api_item(uf="SP")).encode()])
def test_malformed_or_incompatible_success_is_not_evidence_of_absence(body):
    from apps.sources.tasks import check_ilb_listing_availability

    cache.clear()
    listing = old_listing()
    with patch("urllib.request.OpenerDirector.open", return_value=BytesIO(body)):
        assert check_ilb_listing_availability.delay(listing.source_id, listing.pk).get() == "failed"
    assert APIClient().get(f"/out/{listing.pk}/").status_code == 302


@pytest.mark.django_db
@override_settings(**PILOT_SETTINGS)
@pytest.mark.parametrize("change", ["ingestion", "withdrawal", "newer_check", "scope", "source_edit"])
def test_response_is_discarded_if_source_or_offer_changes_during_network_request(change):
    from apps.sources.tasks import check_ilb_listing_availability

    cache.clear()
    listing = old_listing()
    def after_concurrent_change(*args, **kwargs):
        if change == "ingestion":
            persist_listing(listing.source, normalize_listing(build_provider(listing.source).parse(api_item())))
        elif change == "withdrawal":
            listing.source.is_published = False
            listing.source.save()
        elif change == "scope":
            listing.source.collection_scope = "SP:campinas"
            listing.source.save()
        elif change == "newer_check":
            record_availability_check(listing.source, listing.pk, last_seen_at=listing.last_seen_at,
                started_at=timezone.now(), status="available")
        else:
            listing.source.name = "Fonte editada durante a consulta"
            listing.source.save()
        raise missing_response()
    with patch("urllib.request.OpenerDirector.open", side_effect=after_concurrent_change):
        assert check_ilb_listing_availability.delay(listing.source_id, listing.pk).get() == "stale"
    listing.refresh_from_db()
    assert listing.is_active
    if change == "newer_check":
        assert listing.availability_check.status == "available"
    else:
        assert not hasattr(listing, "availability_check")


@pytest.mark.django_db
@override_settings(**PILOT_SETTINGS)
def test_reappearance_in_partial_inventory_reactivates_a_missing_listing_without_new_identity():
    from apps.sources.tasks import check_ilb_listing_availability

    cache.clear()
    listing = old_listing()
    with patch("urllib.request.OpenerDirector.open", side_effect=missing_response()):
        check_ilb_listing_availability.delay(listing.source_id, listing.pk).get()
    updated = persist_listing(listing.source, normalize_listing(build_provider(listing.source).parse(api_item())))
    assert updated.pk == listing.pk and updated.is_active
    assert APIClient().get(f"/out/{listing.pk}/").status_code == 302


@pytest.mark.django_db
@override_settings(**PILOT_SETTINGS)
def test_scheduler_checks_at_most_ten_known_offers_and_advances_to_remaining_candidates():
    from apps.sources.tasks import queue_ilb_availability_checks
    from apps.ingestion.models import ListingAvailabilityCheck

    cache.clear()
    first = old_listing()
    for index in range(11):
        ListingFactory.create(source=first.source, external_id=str(8000000000000 + index))
    Listing.objects.filter(source=first.source).update(last_seen_at=timezone.now() - timedelta(days=2))
    def existing(request, **kwargs):
        external_id = request.full_url.rsplit("/", 1)[1]
        return BytesIO(json.dumps(api_item(id=external_id,
            linkOficial=f"https://venda-imoveis.caixa.gov.br/sistema/detalhe-imovel.asp?hdnimovel={external_id}")).encode())
    with patch("urllib.request.OpenerDirector.open", side_effect=existing) as network:
        assert queue_ilb_availability_checks.delay().get() == 10
        assert ListingAvailabilityCheck.objects.count() == 10
        assert queue_ilb_availability_checks.delay().get() == 2
        assert queue_ilb_availability_checks.delay().get() == 0
    assert network.call_count == 12


@pytest.mark.django_db
@override_settings(**PILOT_SETTINGS)
@pytest.mark.parametrize("disabled", ["flag", "debug", "paused", "withdrawn", "demo"])
def test_disabled_pilot_and_ineligible_sources_never_contact_api(disabled):
    from apps.sources.tasks import check_ilb_listing_availability, queue_ilb_availability_checks

    cache.clear()
    listing = old_listing()
    if disabled in ("paused", "withdrawn", "demo"):
        setattr(listing.source, {"paused": "is_active", "withdrawn": "is_published", "demo": "is_demo"}[disabled], disabled == "demo")
        listing.source.save()
    config = {"ILB_PILOT_ENABLED": False} if disabled == "flag" else {"DEBUG": False} if disabled == "debug" else {}
    with override_settings(**config), patch("urllib.request.OpenerDirector.open", side_effect=AssertionError("No HTTP")):
        assert queue_ilb_availability_checks.delay().get() == 0
        assert check_ilb_listing_availability.delay(listing.source_id, listing.pk).get() == "skipped"


@pytest.mark.django_db
@override_settings(**PILOT_SETTINGS)
def test_check_completed_by_another_worker_before_lock_is_not_downloaded_again():
    from apps.sources.tasks import check_ilb_listing_availability

    cache.clear()
    listing = old_listing()
    backend = caches["default"]
    acquire = backend.add
    completed = False
    def another_worker_finishes(*args, **kwargs):
        nonlocal completed
        if args[0].startswith("ilb:availability:") and not completed:
            completed = True
            with patch.object(backend, "add", side_effect=acquire):
                assert check_ilb_listing_availability.delay(listing.source_id, listing.pk).result == "available"
        return acquire(*args, **kwargs)
    with patch("urllib.request.OpenerDirector.open", return_value=BytesIO(json.dumps(api_item()).encode())) as network:
        with patch.object(backend, "add", side_effect=another_worker_finishes):
            assert check_ilb_listing_availability.delay(listing.source_id, listing.pk).get() == "skipped"
    assert network.call_count == 1


@pytest.mark.django_db
@override_settings(**PILOT_SETTINGS)
@pytest.mark.parametrize("failure", ["open", "404_body"])
def test_transport_failure_never_confirms_absence_and_is_retried(failure):
    from apps.sources.tasks import check_ilb_listing_availability

    cache.clear()
    listing = old_listing()
    class BrokenBody(BytesIO):
        def read(self, *args):
            raise TimeoutError("Response interrupted")
    def disconnected(*args, **kwargs):
        if failure == "open":
            raise URLError("offline")
        raise HTTPError("https://unused.invalid", 404, "Not Found",
                        {"Content-Type": "application/json"}, BrokenBody())
    with patch("urllib.request.OpenerDirector.open", side_effect=disconnected) as network:
        assert check_ilb_listing_availability.delay(listing.source_id, listing.pk).get() == "failed"
    assert network.call_count == 4
    assert APIClient().get(f"/out/{listing.pk}/").status_code == 302


@pytest.mark.django_db
@override_settings(**PILOT_SETTINGS)
def test_individual_removal_preserves_other_source_offer_and_refreshes_property():
    from apps.sources.tasks import check_ilb_listing_availability

    cache.clear()
    listing = old_listing()
    other = ListingFactory.create(property=listing.property, price="500000.00", area="90.00", city="Salvador", state="BA")
    with patch("urllib.request.OpenerDirector.open", side_effect=missing_response()):
        check_ilb_listing_availability.delay(listing.source_id, listing.pk).get()
    response = APIClient().get(f"/api/properties/{listing.property_id}/")
    assert response.status_code == 200
    assert [item["id"] for item in response.json()["listings"]] == [other.pk]
    assert response.json()["area"] == "90.00"
    assert response.json()["min_price"] == "500000.00"


@pytest.mark.django_db
@override_settings(**PILOT_SETTINGS)
def test_availability_uses_the_same_source_rate_budget_as_ingestion():
    from apps.sources.tasks import check_ilb_listing_availability

    cache.clear()
    listing = old_listing()
    listing.source.rate_limit_per_minute = 1
    listing.source.save()
    check_source_rate_limit(listing.source)
    with patch("urllib.request.OpenerDirector.open", side_effect=AssertionError("Budget exhausted")):
        result = check_ilb_listing_availability.delay(listing.source_id, listing.pk)
    assert result.failed() and isinstance(result.result, SourceRateLimitExceeded)
    listing.refresh_from_db()
    assert listing.is_active and not hasattr(listing, "availability_check")
