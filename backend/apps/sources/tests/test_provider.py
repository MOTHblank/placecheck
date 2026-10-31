import pytest
from decimal import Decimal

from apps.sources.normalizers import normalize_listing
from apps.sources.providers import ManualProvider
from apps.sources.schemas import RawListing


def sample_record(external_id="manual-001"):
    return {
        "source_external_id": external_id,
        "title": "  Apartamento  ensolarado ",
        "description": "  Próximo ao metrô. ",
        "transaction_type": "Venda",
        "property_type": "Apartamento",
        "price": "R$ 650.000,00",
        "condominium_fee": "R$ 850,00",
        "iptu": "1.200,00",
        "area": "80,5 m²",
        "bedrooms": "3 dormitórios",
        "bathrooms": "2 banheiros",
        "suites": "1 suíte",
        "parking_spaces": "2 vagas",
        "city": "São Paulo",
        "state": "sp",
        "neighborhood": " Pinheiros ",
        "latitude": "-23,567800",
        "longitude": "-46,691200",
        "url": " https://example.com/listing/manual-001 ",
    }


def test_manual_provider_follows_common_contract():
    provider = ManualProvider({"manual-001": sample_record()})

    references = list(provider.discover())
    raw = provider.parse(provider.fetch(references[0]))

    assert references == ["manual-001"]
    assert isinstance(raw, RawListing)
    assert raw.source_external_id == "manual-001"


def test_normalizer_converts_brazilian_listing_values():
    normalized = normalize_listing(ManualProvider({"manual-001": sample_record()}).parse(sample_record()))

    assert normalized.price == Decimal("650000.00")
    assert normalized.condominium_fee == Decimal("850.00")
    assert normalized.area == Decimal("80.50")
    assert normalized.bedrooms == 3
    assert normalized.transaction_type == "sale"
    assert normalized.property_type == "apartment"
    assert normalized.state == "SP"
    assert normalized.latitude == Decimal("-23.567800")


@pytest.mark.parametrize("price", ["R$ 650.000", "R$650.000,00", 650000, Decimal("650000.00")])
def test_normalizer_handles_plan_prices_without_changing_coordinates(price):
    record = sample_record()
    record.update(price=price, condominium_fee="R$ 1.200", iptu="2.400", latitude=-23.5678)
    normalized = normalize_listing(ManualProvider({}).parse(record))
    assert normalized.price == Decimal("650000.00")
    assert normalized.condominium_fee == Decimal("1200.00")
    assert normalized.iptu == Decimal("2400.00")
    assert normalized.latitude == Decimal("-23.567800")


def test_normalizer_preserves_numeric_decimals_and_missing_values():
    record = sample_record()
    record.update(price=650.125, condominium_fee=None, iptu="", area=80.125)
    normalized = normalize_listing(ManualProvider({}).parse(record))
    assert normalized.price == Decimal("650.12")
    assert normalized.area == Decimal("80.12")
    assert normalized.condominium_fee is None
    assert normalized.iptu is None
