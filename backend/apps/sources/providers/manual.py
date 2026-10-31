from collections.abc import Iterable, Mapping
from typing import Any

from apps.sources.schemas import RawListing

from .base import ListingProvider


class ManualProvider(ListingProvider):
    """Provider inicial para feeds autorizados fornecidos pela aplicação."""

    def __init__(self, records: Mapping[str, Mapping[str, Any]], *, complete: bool = True):
        self.records = records
        self.is_complete_snapshot = complete

    def discover(self) -> Iterable[str]:
        return self.records.keys()

    def fetch(self, reference: str) -> Mapping[str, Any]:
        return self.records[reference]

    def parse(self, payload: Mapping[str, Any]) -> RawListing:
        return RawListing(
            source_external_id=str(payload["source_external_id"]),
            title=payload.get("title"),
            description=payload.get("description"),
            transaction_type=payload.get("transaction_type"),
            property_type=payload.get("property_type"),
            price=payload.get("price"),
            condominium_fee=payload.get("condominium_fee"),
            iptu=payload.get("iptu"),
            area=payload.get("area"),
            bedrooms=payload.get("bedrooms"),
            bathrooms=payload.get("bathrooms"),
            suites=payload.get("suites"),
            parking_spaces=payload.get("parking_spaces"),
            city=payload.get("city"),
            state=payload.get("state"),
            neighborhood=payload.get("neighborhood"),
            latitude=payload.get("latitude"),
            longitude=payload.get("longitude"),
            url=payload["url"],
            sale_method=payload.get("sale_method", ""),
            price_kind=payload.get("price_kind", "asking"),
            source_inventory_date=payload.get("source_inventory_date"),
        )
