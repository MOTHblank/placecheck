from decimal import Decimal
import pytest

from apps.ingestion.services import reconcile_source_listings
from apps.listings.tests.factories import ListingFactory
from apps.properties.services import refresh_property
from apps.properties.tests.factories import PropertyFactory


@pytest.mark.django_db
def test_projection_fills_missing_fields_then_recomputes_after_source_disappears():
    property_ = PropertyFactory.create(area=None, bathrooms=None)
    first = ListingFactory.create(property=property_, area=None, bathrooms=1)
    better = ListingFactory.create(property=property_, area="92", bathrooms=2)
    refresh_property(property_.pk)
    property_.refresh_from_db()
    assert property_.area == Decimal("92")
    assert property_.bathrooms == 2
    reconcile_source_listings(better.source, [])
    property_.refresh_from_db()
    assert property_.area is None
    assert property_.bathrooms == 1
    assert first.is_active
