import pytest
from django.db import IntegrityError

from apps.listings.models import ListingPriceHistory
from apps.listings.tests.factories import ListingFactory


@pytest.mark.django_db
def test_listing_external_id_is_unique_per_source():
    listing = ListingFactory.create()

    with pytest.raises(IntegrityError):
        ListingFactory.create(source=listing.source, external_id=listing.external_id)


@pytest.mark.django_db
def test_same_external_id_can_exist_in_different_sources():
    first = ListingFactory.create()
    second = ListingFactory.create(source=None, external_id=first.external_id)

    assert first.source != second.source


@pytest.mark.django_db
def test_listing_price_history_belongs_to_listing():
    listing = ListingFactory.create()
    history = ListingPriceHistory.objects.create(listing=listing, price="640000.00")

    assert list(listing.price_history.all()) == [history]


@pytest.mark.django_db
def test_admin_prevents_price_and_history_edits(admin_client):
    listing = ListingFactory.create(price="650000.00")
    response = admin_client.get(f"/admin/listings/listing/{listing.pk}/change/")
    assert "price" not in response.context["adminform"].form.fields
    assert "price" in response.context["adminform"].readonly_fields
    response = admin_client.get("/admin/listings/listingpricehistory/add/")
    assert response.status_code == 403
