import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.analytics.models import RedirectEvent
from apps.listings.tests.factories import ListingFactory
from apps.properties.tests.factories import PropertyFactory
from apps.sources.tests.factories import SourceFactory
from apps.listings.models import ListingPriceHistory
from django.utils import timezone
from datetime import timedelta
from django.test import override_settings


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
@override_settings(ANALYTICS_EXCLUDE_ALL=False)
def test_listing_redirect_records_event_and_redirects_to_original(api_client):
    listing = ListingFactory.create(url="https://portal.example/imovel/123")

    response = api_client.get(
        reverse("listing-redirect", args=[listing.pk]),
        HTTP_REFERER="https://placecheck.local/",
        HTTP_USER_AGENT="Mozilla/5.0 Chrome/142.0.0.0",
    )

    assert response.status_code == 302
    assert response["Location"] == listing.url
    event = RedirectEvent.objects.get(listing=listing)
    assert event.source_key == listing.source_id
    assert event.listing_key == listing.pk
    assert event.exposure_id is None
    assert "sessionid" not in response.cookies


@pytest.mark.django_db
def test_openapi_schema_is_available(api_client):
    response = api_client.get(reverse("openapi-schema"), HTTP_ACCEPT="application/json")

    assert response.status_code == 200
    assert response.data["info"]["title"] == "Placecheck API"
    assert "/api/properties/" in response.data["paths"]
    parameters = response.data["paths"]["/api/properties/"]["get"]["parameters"]
    assert {"city", "q", "max_price", "min_area", "ordering", "limit", "offset"} <= {item["name"] for item in parameters}
    redirect = response.data["paths"]["/out/{listing_id}/"]["get"]
    assert "302" in redirect["responses"]
    assert "404" in redirect["responses"]


@pytest.mark.django_db
def test_search_never_combines_sale_and_rent_or_different_offers(api_client):
    property_ = PropertyFactory.create()
    ListingFactory.create(property=property_, price="900000", transaction_type="sale", bedrooms=1)
    ListingFactory.create(property=property_, price="3000", transaction_type="rent", bedrooms=4)
    response = api_client.get("/api/properties/", {"transaction_type": "sale", "max_price": 500000})
    assert response.status_code == 200
    assert response.data["count"] == 0
    response = api_client.get("/api/properties/", {"transaction_type": "sale", "bedrooms": 3})
    assert response.data["count"] == 0
    response = api_client.get("/api/properties/", {"transaction_type": "sale"})
    assert response.data["results"][0]["min_price"] == "900000.00"
    assert response.data["results"][0]["listing_count"] == 1
    response = api_client.get(f"/api/properties/{property_.pk}/", {"transaction_type": "sale"})
    assert len(response.data["listings"]) == 1
    assert response.data["min_price"] == "900000.00"


@pytest.mark.django_db
def test_price_range_must_match_one_offer_and_invalid_values_return_400(api_client):
    property_ = PropertyFactory.create()
    ListingFactory.create(property=property_, price="500000")
    ListingFactory.create(property=property_, price="900000")
    response = api_client.get("/api/properties/", {"min_price": 600000, "max_price": 800000})
    assert response.data["count"] == 0
    for params in ({"min_price": "abc"}, {"bedrooms": -1}, {"min_area": 100, "max_area": 50}):
        assert api_client.get("/api/properties/", params).status_code == 400


@pytest.mark.django_db
def test_details_expose_price_history_and_derived_metrics(api_client):
    listing = ListingFactory.create(price="600000", area="100")
    for days, price in ((30, "650000"), (15, "620000"), (0, "600000")):
        history = ListingPriceHistory.objects.create(listing=listing, price=price)
        ListingPriceHistory.objects.filter(pk=history.pk).update(captured_at=timezone.now() - timedelta(days=days))
    response = api_client.get(f"/api/properties/{listing.property_id}/")
    assert response.status_code == 200
    offer = response.data["listings"][0]
    assert offer["previous_price"] == "620000.00"
    assert offer["lowest_price"] == "600000.00"
    assert offer["highest_price"] == "650000.00"
    assert offer["price_per_m2"] == "6000.00"
    assert offer["price_drop_percent"] == pytest.approx(7.69230769)
    assert len(offer["price_history"]) == 3


@pytest.mark.django_db
def test_additional_filters_and_ordering_use_matching_offers(api_client):
    small = ListingFactory.create(area="50", bathrooms=1, parking_spaces=0, price="500000")
    large = ListingFactory.create(area="100", bathrooms=3, parking_spaces=2, price="600000")
    response = api_client.get("/api/properties/", {"min_area": 80, "bathrooms": 2, "parking_spaces": 1})
    assert [item["id"] for item in response.data["results"]] == [large.property_id]
    response = api_client.get("/api/properties/", {"ordering": "price_per_m2"})
    assert [item["id"] for item in response.data["results"]] == [large.property_id, small.property_id]


@pytest.mark.django_db
def test_source_pause_preserves_publication_but_withdrawal_hides_only_its_offers(api_client):
    from apps.properties.services import refresh_property

    property_ = PropertyFactory.create()
    withdrawn = ListingFactory.create(property=property_, area="90", description="Restricted", price="500000")
    retained = ListingFactory.create(property=property_, area="100", price="600000")
    source = withdrawn.source
    source.is_active = False
    source.save()
    assert api_client.get(f"/out/{withdrawn.pk}/").status_code == 302
    source.is_published = False
    source.save()
    response = api_client.get(f"/api/properties/{property_.pk}/")
    assert response.status_code == 200
    assert response.data["listing_count"] == 1
    assert response.data["min_price"] == "600000.00"
    assert response.data["area"] == "100.00"
    assert [offer["id"] for offer in response.data["listings"]] == [retained.pk]
    assert api_client.get(f"/out/{withdrawn.pk}/").status_code == 404
    retained.source.is_published = False
    retained.source.save()
    assert api_client.get(f"/api/properties/{property_.pk}/").status_code == 404
    assert api_client.get("/api/properties/").data["count"] == 0


@pytest.mark.django_db
def test_revocation_removes_stored_content_and_history(api_client):
    from apps.ingestion.services import persist_listing
    from apps.sources.normalizers import normalize_listing
    from apps.sources.providers import ManualProvider
    from apps.sources.tests.test_provider import sample_record

    source = SourceFactory.create(can_store_description=True)
    normalized = normalize_listing(ManualProvider({}).parse(sample_record()))
    listing = persist_listing(source, normalized)
    assert listing.description
    assert listing.price_history.count() == 1
    source.can_store_description = False
    source.can_retain_price_history = False
    source.save()
    listing.refresh_from_db()
    assert listing.description == ""
    assert listing.price_history.count() == 0
    listing = persist_listing(source, normalized)
    assert listing.description == ""
    assert listing.price_history.count() == 0
    offer = api_client.get(f"/api/properties/{listing.property_id}/").data["listings"][0]
    assert offer["description"] == ""
    assert offer["price_history"] == []
