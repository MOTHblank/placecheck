import re
from decimal import Decimal, InvalidOperation

from apps.sources.schemas import NormalizedListing, RawListing


def _decimal(value: object | None) -> Decimal | None:
    if value is None or value == "":
        return None
    number = _parse_decimal(value)
    return number.quantize(Decimal("0.01")) if number is not None else None


def _money(value: object | None) -> Decimal | None:
    # Brazilian strings may omit cents. Numeric inputs always use decimal dots.
    if isinstance(value, str):
        text = value.strip().replace("R$", "").strip()
        if re.fullmatch(r"-?\d{1,3}(?:\.\d{3})+", text):
            value = text.replace(".", "")
    return _decimal(value)


def _parse_decimal(value: object | None) -> Decimal | None:
    if value is None or value == "":
        return None
    if isinstance(value, Decimal):
        return value
    text = re.sub(r"[^0-9,.-]", "", str(value).strip().replace("R$", ""))
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    try:
        return Decimal(text)
    except InvalidOperation as error:
        raise ValueError(f"Valor decimal inválido: {value!r}") from error


def _integer(value: object | None) -> int | None:
    if value is None or value == "":
        return None
    match = re.search(r"\d+", str(value))
    return int(match.group()) if match else None


def _coordinate(value: object | None) -> Decimal | None:
    coordinate = _parse_decimal(value)
    return coordinate.quantize(Decimal("0.000001")) if coordinate is not None else None


def _text(value: str | None) -> str:
    return " ".join((value or "").split())


def normalize_listing(raw: RawListing) -> NormalizedListing:
    transaction_type = _text(raw.transaction_type).lower()
    property_type = _text(raw.property_type).lower()
    return NormalizedListing(
        source_external_id=raw.source_external_id.strip(),
        title=_text(raw.title),
        description=_text(raw.description),
        transaction_type={"venda": "sale", "aluguel": "rent"}.get(transaction_type, transaction_type),
        property_type={"apartamento": "apartment", "casa": "house", "terreno": "land"}.get(property_type, property_type),
        price=_money(raw.price),
        condominium_fee=_money(raw.condominium_fee),
        iptu=_money(raw.iptu),
        area=_decimal(raw.area),
        bedrooms=_integer(raw.bedrooms),
        bathrooms=_integer(raw.bathrooms),
        suites=_integer(raw.suites),
        parking_spaces=_integer(raw.parking_spaces),
        city=_text(raw.city),
        state=_text(raw.state).upper(),
        neighborhood=_text(raw.neighborhood),
        latitude=_coordinate(raw.latitude),
        longitude=_coordinate(raw.longitude),
        url=raw.url.strip(),
    )
