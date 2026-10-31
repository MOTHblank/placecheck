from decimal import Decimal
from unittest.mock import patch
from io import BytesIO
from urllib.error import HTTPError, URLError

import pytest
from django.core.cache import cache, caches
from django.test import override_settings

from apps.sources.normalizers import normalize_listing
from apps.ingestion.exceptions import ProviderTemporaryError
from apps.sources.providers.imoveis_leilao_brasil import ImoveisLeilaoBrasilClient, ImoveisLeilaoBrasilProvider


def api_item(**changes):
    item = {
        "id": "1234567890123", "tipoSlug": "apartamento", "tipo": "Apartamento",
        "cidade": "Salvador", "cidadeSlug": "salvador", "uf": "BA", "bairro": "Centro",
        "preco": 33398.37, "areaPrivativa": 49.25, "quartos": 2, "vagas": None,
        "modalidade": "Venda Direta Online",
        "linkOficial": "https://venda-imoveis.caixa.gov.br/sistema/detalhe-imovel.asp?hdnimovel=1234567890123",
        "descricao": "Informação não retida", "endereco": "Endereço não retido",
    }
    return item | changes


class CatalogClient:
    def __init__(self, items, *, total=300):
        self.items = items
        self.total = total

    def search(self, *, uf, city, limit):
        return {"total": self.total, "pagina": 1, "limite": limit,
                "listaGeradaEm": "2026-10-29", "resultados": self.items}


@override_settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}})
def test_real_api_shape_normalizes_without_private_fields_or_claiming_completeness():
    cache.clear()
    provider = ImoveisLeilaoBrasilProvider(uf="BA", city="salvador", limit=2,
                                          client=CatalogClient([api_item()]))
    references = list(provider.discover())
    payload = provider.fetch(references[0])
    normalized = normalize_listing(provider.parse(payload))
    assert normalized.source_external_id == "1234567890123"
    assert normalized.price == Decimal("33398.37")
    assert normalized.area == Decimal("49.25")
    assert normalized.parking_spaces is None
    assert normalized.transaction_type == "sale"
    assert normalized.description == ""
    assert normalized.sale_method == "venda-direta-online"
    assert normalized.price_kind == "asking"
    assert not provider.is_complete_snapshot
    assert "endereco" not in payload and "descricao" not in payload


@pytest.mark.parametrize(("method", "kind"), [
    ("Leilão SFI", "minimum"), ("Licitação Aberta", "minimum"),
    ("Venda Online", "reference"), ("Venda Direta Online", "asking"),
])
def test_sale_method_is_preserved_without_treating_minimum_bids_as_asking_prices(method, kind):
    provider = ImoveisLeilaoBrasilProvider(uf="BA", city="salvador")
    normalized = normalize_listing(provider.parse(api_item(modalidade=method)))
    assert normalized.price_kind == kind
    assert normalized.transaction_type == "sale"


@pytest.mark.parametrize("changes", [
    {"id": "invalid"}, {"uf": "SP"}, {"cidade": "Feira de Santana"},
    {"preco": -1}, {"preco": float("nan")}, {"quartos": -2}, {"quartos": 1.5},
    {"vagas": True}, {"areaPrivativa": "49 m²"}, {"modalidade": "Aluguel"},
    {"modalidadeSlug": "leilao-sfi"}, {"tipoSlug": "unknown"},
    {"linkOficial": "https://example.com/"}, {"linkOficial": ""},
    {"linkOficial": "https://venda-imoveis.caixa.gov.br/sistema/detalhe-imovel.asp?hdnimovel=9999999999999"},
    {"linkOficial": "https://venda-imoveis.caixa.gov.br/sistema/detalhe-imovel.asp?hdnimovel=1234567890123&token=secret"},
])
def test_invalid_api_data_fails_instead_of_creating_plausible_listings(changes):
    with pytest.raises(ValueError):
        ImoveisLeilaoBrasilProvider(uf="BA", city="salvador").parse(api_item(**changes))


@override_settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}})
def test_tasks_reuse_sanitized_immutable_capture_and_daily_cache():
    cache.clear()
    first_client = CatalogClient([api_item()])
    first = ImoveisLeilaoBrasilProvider(uf="BA", city="salvador", client=first_client)
    references = list(first.discover())
    first_client.items[0]["preco"] = 999999
    # A new worker/provider must not re-read the changed API while processing this capture.
    class OfflineClient:
        def search(self, **kwargs):
            raise AssertionError("Cached capture should not contact the service again")
    second = ImoveisLeilaoBrasilProvider(uf="BA", city="salvador", client=OfflineClient())
    assert second.parse(second.fetch(references[0])).price == Decimal("33398.37")
    assert list(second.discover()) == references
    with pytest.raises(ValueError):
        ImoveisLeilaoBrasilProvider(uf="SP", city="campinas").fetch(references[0])
    cache.clear()
    with pytest.raises(ValueError):
        second.fetch(references[0])


@override_settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}})
def test_capture_completed_by_another_worker_before_lock_acquisition_is_reused():
    cache.clear()
    producer = ImoveisLeilaoBrasilProvider(uf="BA", city="salvador", client=CatalogClient([api_item()]))
    class OfflineClient:
        def search(self, **kwargs):
            raise AssertionError("Another worker already fetched this day's catalog")
    consumer = ImoveisLeilaoBrasilProvider(uf="BA", city="salvador", client=OfflineClient())
    backend = caches["default"]
    acquire = backend.add
    produced = []
    def acquire_after_other_worker(*args, **kwargs):
        # Model another process completing its capture between our cache read and lock acquisition.
        with patch.object(backend, "add", side_effect=acquire):
            produced.extend(producer.discover())
        return acquire(*args, **kwargs)
    with patch.object(backend, "add", side_effect=acquire_after_other_worker):
        assert list(consumer.discover()) == produced


@override_settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}})
@pytest.mark.parametrize("items", [[api_item(), api_item()], [api_item(preco=-1)]])
def test_bad_capture_does_not_become_a_cached_inventory(items):
    cache.clear()
    provider = ImoveisLeilaoBrasilProvider(uf="BA", city="salvador", client=CatalogClient(items))
    with pytest.raises(ValueError):
        list(provider.discover())
    assert not provider.is_complete_snapshot


@pytest.mark.parametrize("failure", [
    HTTPError("https://unused.invalid", 429, "rate", {}, None),
    HTTPError("https://unused.invalid", 503, "down", {}, None), URLError("offline"),
])
def test_api_transient_errors_are_retryable_and_sanitized(failure):
    with patch("urllib.request.OpenerDirector.open", side_effect=failure):
        with pytest.raises(ProviderTemporaryError, match="ILB"):
            ImoveisLeilaoBrasilClient().search(uf="BA", city="salvador", limit=2)


@pytest.mark.parametrize("response", [b"<html>blocked</html>", b"x" * 1_048_577])
def test_api_invalid_or_oversized_response_is_not_empty_inventory(response):
    with patch("urllib.request.OpenerDirector.open", return_value=BytesIO(response)):
        with pytest.raises(ValueError):
            ImoveisLeilaoBrasilClient().search(uf="BA", city="salvador", limit=2)


def test_api_client_identifies_itself_and_requests_one_filtered_page():
    with patch("urllib.request.OpenerDirector.open", return_value=BytesIO(b'{"resultados": []}')) as network:
        assert ImoveisLeilaoBrasilClient().search(uf="BA", city="salvador", limit=2) == {"resultados": []}
    request = network.call_args.args[0]
    assert request.full_url == "https://www.imoveisleilaobrasil.com.br/api/imoveis?uf=ba&cidade=salvador&limite=2&pagina=1&ordem=preco-menor"
    assert request.get_header("User-agent").startswith("Placecheck/")
