from io import BytesIO
import json
from unittest.mock import patch

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
from .test_ilb_provider import api_item


PILOT_SETTINGS = dict(
    DEBUG=True, ILB_PILOT_ENABLED=True, ILB_PILOT_UF="BA", ILB_PILOT_CITY="salvador", ILB_PILOT_LIMIT=2,
    CELERY_TASK_ALWAYS_EAGER=True,
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
)


def response(items):
    return BytesIO(json.dumps({"total": len(items), "pagina": 1, "limite": 2,
                              "listaGeradaEm": "2026-10-29", "resultados": items}).encode())


@pytest.mark.django_db
@override_settings(**PILOT_SETTINGS)
def test_async_pilot_is_searchable_idempotent_partial_and_withdrawable():
    cache.clear()
    call_command("setup_ilb_pilot")
    source = Source.objects.get(slug=SOURCE_SLUG)
    assert not source.can_retain_price_history and not source.can_store_description and not source.is_demo
    client = APIClient()
    with patch("urllib.request.OpenerDirector.open", return_value=response([api_item(modalidade="Leilão SFI")])):
        assert sync_source.delay(source.pk).get() == 1
    page = client.get("/api/properties/", {"city": "Salvador", "transaction_type": "sale"}).json()
    assert page["count"] == 1
    assert page["results"][0]["has_special_sale"] is True
    property_id = page["results"][0]["id"]
    offer = client.get(f"/api/properties/{property_id}/").json()["listings"][0]
    assert offer["price"] == "33398.37"
    assert offer["price_kind"] == "minimum" and offer["sale_method"] == "leilao-sfi"
    assert "CAIXA" in offer["attribution_text"]
    assert offer["source_url"] == "https://www.imoveisleilaobrasil.com.br/api"
    assert offer["source_inventory_date"] == "2026-10-29"
    assert offer["description"] == "" and offer["price_history"] == []
    assert source.sync_runs.latest("id").status == "partial"
    with patch("urllib.request.OpenerDirector.open", side_effect=AssertionError("Cached capture")):
        assert sync_source.delay(source.pk).get() == 1
    assert client.get("/api/properties/").json()["count"] == 1
    cache.clear()
    with patch("urllib.request.OpenerDirector.open", return_value=response([api_item(preco=32000, modalidade="Leilão SFI")])):
        sync_source.delay(source.pk).get()
    updated = client.get(f"/api/properties/{property_id}/").json()["listings"][0]
    assert updated["id"] == offer["id"] and updated["price"] == "32000.00"
    assert updated["price_history"] == []  # retention is explicitly disabled for this pilot
    cache.clear()
    with patch("urllib.request.OpenerDirector.open", return_value=response([])):
        sync_source.delay(source.pk).get()
    assert client.get("/api/properties/").json()["count"] == 1
    redirect = client.get(f"/out/{offer['id']}/")
    assert redirect.status_code == 302 and redirect["Location"] == api_item()["linkOficial"]
    assert client.get("/api/properties/", {"transaction_type": "rent"}).json()["count"] == 0
    source.is_active = False
    source.is_published = False
    source.save()
    assert client.get("/api/properties/").json()["count"] == 0
    assert client.get(f"/out/{offer['id']}/").status_code == 404


@pytest.mark.django_db
@override_settings(**PILOT_SETTINGS)
def test_pilot_configuration_cannot_silently_change_market_or_activate_outside_local_mode():
    call_command("setup_ilb_pilot")
    source = Source.objects.get(slug=SOURCE_SLUG)
    with override_settings(ILB_PILOT_CITY="campinas", ILB_PILOT_UF="SP"):
        with pytest.raises(CommandError):
            call_command("setup_ilb_pilot")
        with pytest.raises(ImproperlyConfigured):
            build_provider(source)
    for config in ({"ILB_PILOT_ENABLED": False}, {"DEBUG": False}):
        with override_settings(**config):
            with pytest.raises(CommandError):
                call_command("setup_ilb_pilot")
            with pytest.raises(ImproperlyConfigured):
                build_provider(source)
