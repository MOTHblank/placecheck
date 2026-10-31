from decimal import Decimal

import pytest

from apps.deduplication.services import (
    SIMILARITY_THRESHOLD,
    calculate_similarity,
    match_listing_to_property,
)
from apps.listings.tests.factories import ListingFactory
from apps.properties.models import Property
from apps.sources.tests.factories import SourceFactory


@pytest.mark.django_db
def test_equivalent_listings_from_different_sources_share_property():
    first = ListingFactory.create(source=SourceFactory.create(slug="fonte-a"), property=None)
    second = ListingFactory.create(
        source=SourceFactory.create(slug="fonte-b"),
        property=None,
        external_id="listing-002",
    )

    first_property = match_listing_to_property(first)
    second_property = match_listing_to_property(second)

    assert second_property == first_property
    assert second.property_id == first.property_id


@pytest.mark.django_db
def test_different_properties_do_not_cross_threshold():
    first = ListingFactory.create(property=None, area=Decimal("80.00"), bedrooms=2)
    second = ListingFactory.create(
        source=SourceFactory.create(slug="outra-fonte"),
        property=None,
        external_id="listing-002",
        neighborhood="Moema",
        area=Decimal("180.00"),
        bedrooms=4,
    )

    result = calculate_similarity(first, second)

    assert result.score < SIMILARITY_THRESHOLD


@pytest.mark.django_db
def test_first_listing_creates_a_property():
    listing = ListingFactory.create(property=None)

    property_ = match_listing_to_property(listing)

    assert isinstance(property_, Property)
    assert property_.city == listing.city
    assert listing.refresh_from_db() is None
    assert listing.property_id == property_.id
