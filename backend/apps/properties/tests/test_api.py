import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.analytics.models import RedirectEvent
from apps.listings.tests.factories import ListingFactory
from apps.properties.tests.factories import PropertyFactory
from apps.sources.tests.factories import SourceFactory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
def test_property_list_supports_filters_pagination_and_offers(api_client):
    property_ = PropertyFactory.create(city="São Paulo", bedrooms=2)
    ListingFactory.create(property=property_, price="650000.00", transaction_type="sale")
    other = PropertyFactory.create(city="Campinas")
    ListingFactory.create(property=other, price="300000.00", transaction_type="sale")

    response = api_client.get(
        reverse("properties:property-list"),
        {"city": "São Paulo", "min_price": "600000", "limit": 1},
    )

    assert response.status_code == 200
    assert response.data["count"] == 1
    assert len(response.data["results"]) == 1
    assert response.data["results"][0]["listing_count"] == 1
    assert response.data["results"][0]["min_price"] == "650000.00"


@pytest.mark.django_db
def test_property_detail_returns_active_offers(api_client):
    property_ = PropertyFactory.create()
    listing = ListingFactory.create(property=property_, source=SourceFactory.create(slug="detail-source"))

    response = api_client.get(reverse("properties:property-detail", args=[property_.pk]))

    assert response.status_code == 200
    assert response.data["id"] == property_.pk
    assert response.data["listings"][0]["id"] == listing.pk
    assert response.data["listings"][0]["source"] == "Fonte manual"


@pytest.mark.django_db
def test_listing_redirect_records_event_and_redirects_to_original(api_client):
    listing = ListingFactory.create(url="https://portal.example/imovel/123")

    response = api_client.get(
        reverse("listing-redirect", args=[listing.pk]),
        HTTP_REFERER="https://placecheck.local/",
        HTTP_USER_AGENT="pytest",
    )

    assert response.status_code == 302
    assert response["Location"] == listing.url
    event = RedirectEvent.objects.get(listing=listing)
    assert event.referer == "https://placecheck.local/"
    assert event.user_agent == "pytest"
    assert event.session_id


@pytest.mark.django_db
def test_openapi_schema_is_available(api_client):
    response = api_client.get(reverse("openapi-schema"), HTTP_ACCEPT="application/json")

    assert response.status_code == 200
    assert response.data["info"]["title"] == "Placecheck API"
    assert "/api/properties/" in response.data["paths"]
