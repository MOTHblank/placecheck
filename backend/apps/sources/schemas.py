from dataclasses import dataclass
from decimal import Decimal
from datetime import date


@dataclass(frozen=True)
class RawListing:
    source_external_id: str
    title: str | None
    description: str | None
    transaction_type: str | None
    property_type: str | None
    price: object | None
    condominium_fee: object | None
    iptu: object | None
    area: object | None
    bedrooms: object | None
    bathrooms: object | None
    suites: object | None
    parking_spaces: object | None
    city: str | None
    state: str | None
    neighborhood: str | None
    latitude: object | None
    longitude: object | None
    url: str
    sale_method: str = ""
    price_kind: str = "asking"
    source_inventory_date: str | None = None


@dataclass(frozen=True)
class NormalizedListing:
    source_external_id: str
    title: str
    description: str
    transaction_type: str
    property_type: str
    price: Decimal | None
    condominium_fee: Decimal | None
    iptu: Decimal | None
    area: Decimal | None
    bedrooms: int | None
    bathrooms: int | None
    suites: int | None
    parking_spaces: int | None
    city: str
    state: str
    neighborhood: str
    latitude: Decimal | None
    longitude: Decimal | None
    url: str
    sale_method: str = ""
    price_kind: str = "asking"
    source_inventory_date: date | None = None
