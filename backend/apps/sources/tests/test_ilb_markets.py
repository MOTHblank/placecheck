from io import BytesIO
import json
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

import pytest
from django.core.cache import cache
from django.core.management import call_command
from django.core.management.base import CommandError
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings
from rest_framework.test import APIClient

from apps.ingestion.tasks import sync_source
from apps.sources.models import Source
from apps.sources.providers.imoveis_leilao_brasil import SOURCE_SLUG
from apps.sources.providers.registry import build_provider
from apps.ingestion.exceptions import SourceRateLimitExceeded
from .test_ilb_pipeline import PILOT_SETTINGS
from .test_ilb_provider import api_item


MARKETS = "BA:salvador,SP:campinas"


def market_response(request, **kwargs):
    query = parse_qs(urlsplit(request.full_url).query)
    if query["cidade"] == ["campinas"]:
        item = api_item(id="9876543210123", cidade="Campinas", cidadeSlug="campinas", uf="SP",
            linkOficial="https://venda-imoveis.caixa.gov.br/sistema/detalhe-imovel.asp?hdnimovel=9876543210123")
    else:
        item = api_item()
    return BytesIO(json.dumps({"total": 100, "pagina": 1, "limite": 2,
                              "listaGeradaEm": "2026-11-03", "resultados": [item]}).encode())


@pytest.mark.django_db
@override_settings(**PILOT_SETTINGS, ILB_PILOT_MARKETS=MARKETS)
def test_two_explicit_markets_share_one_source_and_are_searchable_in_one_inventory():
    cache.clear()
    call_command("setup_ilb_pilot")
    source = Source.objects.get(slug=SOURCE_SLUG)
    with patch("urllib.request.OpenerDirector.open", side_effect=market_response) as network:
        assert sync_source.delay(source.pk).get() == 2
    assert network.call_count == 2
    client = APIClient()
    inventory = client.get("/api/properties/", {"transaction_type": "sale"}).json()
    assert inventory["count"] == 2
    assert {(item["city"], item["state"]) for item in inventory["results"]} == {("Salvador", "BA"), ("Campinas", "SP")}
    assert client.get("/api/properties/", {"city": "Campinas", "state": "SP"}).json()["count"] == 1
    assert Source.objects.count() == 1 and source.listings.count() == 2
    assert source.collection_scope == "BA:salvador|SP:campinas"
    assert source.sync_runs.latest("id").status == "partial"
    with patch("urllib.request.OpenerDirector.open", side_effect=AssertionError("Daily cache")):
        assert sync_source.delay(source.pk).get() == 2
    assert source.listings.count() == 2


@pytest.mark.django_db
@override_settings(**PILOT_SETTINGS, ILB_PILOT_MARKETS=MARKETS)
def test_partial_market_failure_never_persists_half_a_discovery_or_reconciles_absences():
    cache.clear()
    call_command("setup_ilb_pilot")
    source = Source.objects.get(slug=SOURCE_SLUG)
    with patch("urllib.request.OpenerDirector.open", side_effect=market_response):
        sync_source.delay(source.pk).get()
    before = list(source.listings.order_by("id").values("id", "last_seen_at", "is_active"))
    cache.clear()

    def failing_market(request, **kwargs):
        if parse_qs(urlsplit(request.full_url).query)["cidade"] == ["campinas"]:
            return BytesIO(b'{"invalid":"response"}')
        return market_response(request, **kwargs)

    with patch("urllib.request.OpenerDirector.open", side_effect=failing_market):
        with pytest.raises(ValueError):
            sync_source.delay(source.pk).get()
    assert source.sync_runs.latest("id").status == "failed"
    assert list(source.listings.order_by("id").values("id", "last_seen_at", "is_active")) == before


@pytest.mark.django_db
@override_settings(**PILOT_SETTINGS, ILB_PILOT_MARKETS=MARKETS)
def test_market_order_is_canonical_and_existing_scope_cannot_be_replaced():
    call_command("setup_ilb_pilot")
    source = Source.objects.get(slug=SOURCE_SLUG)
    with override_settings(ILB_PILOT_MARKETS=" SP:campinas , BA:salvador "):
        call_command("setup_ilb_pilot")
        assert build_provider(source).collection_scope == source.collection_scope
    with override_settings(ILB_PILOT_MARKETS="BA:salvador"):
        with pytest.raises(CommandError):
            call_command("setup_ilb_pilot")
        with pytest.raises(ImproperlyConfigured):
            build_provider(source)


@pytest.mark.django_db
@override_settings(**PILOT_SETTINGS)
@pytest.mark.parametrize("markets", ["BA:salvador,BA:salvador", "BA:salvador,SP:campinas,RJ:rio", "SP", "SP:campinas,", "XX:campinas"])
def test_invalid_allowlist_fails_before_source_creation(markets):
    with override_settings(ILB_PILOT_MARKETS=markets), pytest.raises(CommandError):
        call_command("setup_ilb_pilot")
    assert not Source.objects.exists()


@pytest.mark.django_db
@override_settings(**PILOT_SETTINGS, ILB_PILOT_MARKETS=MARKETS)
def test_joint_discovery_charges_shared_source_budget_for_second_market():
    cache.clear()
    call_command("setup_ilb_pilot")
    source = Source.objects.get(slug=SOURCE_SLUG)
    with patch("apps.sources.providers.registry.check_source_rate_limit", side_effect=SourceRateLimitExceeded), patch(
        "urllib.request.OpenerDirector.open", side_effect=market_response
    ) as network:
        with pytest.raises(SourceRateLimitExceeded):
            build_provider(source).discover()
    assert network.call_count == 1 and not source.listings.exists()


@pytest.mark.django_db
@override_settings(**PILOT_SETTINGS, ILB_PILOT_MARKETS=MARKETS)
def test_individual_availability_accepts_both_markets_but_rejects_other_cities():
    call_command("setup_ilb_pilot")
    provider = build_provider(Source.objects.get(slug=SOURCE_SLUG))
    for city, slug, state in [("Salvador", "salvador", "BA"), ("Campinas", "campinas", "SP")]:
        with patch("urllib.request.OpenerDirector.open", return_value=BytesIO(json.dumps(
            api_item(cidade=city, cidadeSlug=slug, uf=state)).encode())):
            assert provider.check_availability("1234567890123")
    with patch("urllib.request.OpenerDirector.open", return_value=BytesIO(json.dumps(
        api_item(cidade="Santos", cidadeSlug="santos", uf="SP")).encode())):
        with pytest.raises(ValueError):
            provider.check_availability("1234567890123")


@pytest.mark.django_db
@override_settings(**PILOT_SETTINGS, ILB_PILOT_MARKETS=MARKETS)
def test_joint_inventory_withdrawal_removes_both_markets_and_preserves_permissions():
    cache.clear()
    call_command("setup_ilb_pilot")
    source = Source.objects.get(slug=SOURCE_SLUG)
    with patch("urllib.request.OpenerDirector.open", side_effect=market_response):
        sync_source.delay(source.pk).get()
    client = APIClient()
    offers = list(source.listings.values("id", "property_id"))
    source.is_published = False
    source.save()
    assert client.get("/api/properties/").json()["count"] == 0
    for offer in offers:
        assert client.get(f"/api/properties/{offer['property_id']}/").status_code == 404
        assert client.get(f"/out/{offer['id']}/").status_code == 404
    source.refresh_from_db()
    assert source.listings.count() == 2
    assert not source.can_retain_price_history and not source.can_store_description
    source.is_published = True
    source.save()
    assert client.get("/api/properties/").json()["count"] == 2


@pytest.mark.django_db
@override_settings(**PILOT_SETTINGS, ILB_PILOT_MARKETS=MARKETS)
def test_market_rate_limit_must_allow_discovery_to_make_progress():
    call_command("setup_ilb_pilot")
    source = Source.objects.get(slug=SOURCE_SLUG)
    source.rate_limit_per_minute = 1
    source.save()
    with pytest.raises(ImproperlyConfigured):
        build_provider(source)


@pytest.mark.django_db
@override_settings(**PILOT_SETTINGS, ILB_PILOT_MARKETS=MARKETS, ILB_PILOT_PRICE_HISTORY=True)
def test_opted_in_internal_price_history_is_idempotent_and_revocable():
    cache.clear()
    call_command("setup_ilb_pilot")
    source = Source.objects.get(slug=SOURCE_SLUG)
    with patch("urllib.request.OpenerDirector.open", side_effect=market_response):
        sync_source.delay(source.pk).get()
    listing = source.listings.get(city="Salvador")
    initial_price = listing.price
    assert listing.price_history.count() == 1
    with patch("urllib.request.OpenerDirector.open", side_effect=AssertionError("Daily cache")):
        sync_source.delay(source.pk).get()
    assert listing.price_history.count() == 1

    def changed_market(request, **kwargs):
        response = market_response(request, **kwargs)
        payload = json.loads(response.read())
        if parse_qs(urlsplit(request.full_url).query)["cidade"] == ["salvador"]:
            payload["resultados"][0]["preco"] = 31000
        return BytesIO(json.dumps(payload).encode())

    cache.clear()
    with patch("urllib.request.OpenerDirector.open", side_effect=changed_market):
        sync_source.delay(source.pk).get()
    listing.refresh_from_db()
    assert listing.price == 31000
    assert list(listing.price_history.order_by("id").values_list("price", flat=True)) == [initial_price, 31000]
    assert source.listings.get(city="Campinas").price_history.count() == 1
    client = APIClient()
    detail = client.get(f"/api/properties/{listing.property_id}/").json()
    assert len(detail["listings"][0]["price_history"]) == 2
    with override_settings(ILB_PILOT_PRICE_HISTORY=False):
        call_command("setup_ilb_pilot")
    source.refresh_from_db()
    assert not source.can_retain_price_history
    assert listing.price_history.count() == 0
    assert source.listings.get(city="Campinas").price_history.count() == 0
