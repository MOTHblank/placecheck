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
    first = ListingFactory.create(source=SourceFactory.create(slug="fonte-a"), property=None, latitude="-23.561000", longitude="-46.690000", title="Apartamento em Pinheiros unidade 401")
    second = ListingFactory.create(
        source=SourceFactory.create(slug="fonte-b"),
        property=None,
        external_id="listing-002",
        latitude="-23.561000", longitude="-46.690000", title="Apartamento em Pinheiros unidade 401",
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


@pytest.mark.django_db
def test_generic_characteristics_without_identity_evidence_never_auto_merge():
    first = ListingFactory.create(property=None, area=None)
    second = ListingFactory.create(property=None, area=None, source=SourceFactory.create())
    assert match_listing_to_property(first) != match_listing_to_property(second)


@pytest.mark.django_db
def test_corrected_listing_can_leave_a_bad_group_and_retains_decision_history():
    first = ListingFactory.create(property=None, latitude="-23.561000", longitude="-46.690000", title="Apartamento em Pinheiros unidade 401")
    second = ListingFactory.create(property=None, source=SourceFactory.create(), latitude="-23.561000", longitude="-46.690000", title="Apartamento em Pinheiros unidade 401")
    shared = match_listing_to_property(first)
    assert match_listing_to_property(second) == shared
    second.area = Decimal("160")
    second.save()
    assert match_listing_to_property(second) != shared
    assert second.match_decisions.filter(outcome="automatic").exists()
    decision = second.match_decisions.latest("id")
    assert decision.previous_property_id == shared.pk
    assert decision.assigned_property_id == second.property_id


@pytest.mark.django_db
def test_better_data_can_merge_previously_separate_listings():
    first = ListingFactory.create(property=None, area=None, latitude="-23.561000", longitude="-46.690000", title="Apartamento em Pinheiros unidade 401")
    second = ListingFactory.create(property=None, source=SourceFactory.create(), latitude="-23.561000", longitude="-46.690000", title="Apartamento em Pinheiros unidade 401")
    assert match_listing_to_property(first) != match_listing_to_property(second)
    first.area = Decimal("80")
    first.save()
    assert match_listing_to_property(first) == second.property


@pytest.mark.django_db
def test_same_building_but_incompatible_characteristics_do_not_merge():
    first = ListingFactory.create(property=None, latitude="-23.561000", longitude="-46.690000", title="Apartamento em Pinheiros unidade 401")
    second = ListingFactory.create(property=None, source=SourceFactory.create(), latitude="-23.561000", longitude="-46.690000", title="Apartamento em Pinheiros unidade 401", bedrooms=3)
    assert match_listing_to_property(first) != match_listing_to_property(second)


@pytest.mark.django_db
def test_generic_titles_even_at_same_coordinates_require_review():
    first = ListingFactory.create(property=None, latitude="-23.561000", longitude="-46.690000")
    second = ListingFactory.create(property=None, source=SourceFactory.create(), latitude="-23.561000", longitude="-46.690000")
    assert match_listing_to_property(first) != match_listing_to_property(second)
    assert second.match_decisions.latest("id").outcome == "possible"
