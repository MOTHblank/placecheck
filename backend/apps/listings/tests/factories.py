from apps.listings.models import Listing

from apps.properties.tests.factories import PropertyFactory
from apps.sources.tests.factories import SourceFactory


class ListingFactory:
    @staticmethod
    def create(**kwargs):
        source = kwargs.pop("source", None) or SourceFactory.create()
        property_ = kwargs.pop("property", ...)
        if property_ is ...:
            property_ = PropertyFactory.create()
        values = {
            "source": source,
            "property": property_,
            "external_id": "listing-001",
            "title": "Apartamento em Pinheiros",
            "transaction_type": Listing.TransactionType.SALE,
            "property_type": "apartment",
            "price": "650000.00",
            "area": "80.00",
            "bedrooms": 2,
            "bathrooms": 2,
            "parking_spaces": 1,
            "city": "São Paulo",
            "state": "SP",
            "neighborhood": "Pinheiros",
            "url": "https://example.com/listings/listing-001",
        }
        values.update(kwargs)
        return Listing.objects.create(**values)
