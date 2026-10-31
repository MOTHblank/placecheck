from io import StringIO

import pytest
from django.core.management import call_command
from django.db.models import Count
from rest_framework.test import APIClient

from apps.listings.models import Listing, ListingPriceHistory
from apps.properties.models import Property
from apps.sources.models import Source
from apps.sources.tests.factories import SourceFactory


@pytest.mark.django_db
def test_demo_seed_covers_search_comparison_history_and_inactive_offers():
    call_command("seed_demo", stdout=StringIO())

    assert Source.objects.count() == 3
    assert not Source.objects.filter(is_active=True).exists()
    assert Property.objects.count() == 30
    assert Listing.objects.count() == 60
    assert set(Listing.objects.values_list("transaction_type", flat=True)) == {"sale", "rent"}
    assert Listing.objects.filter(price__isnull=True).exists()
    assert Listing.objects.filter(is_active=False).exists()
    assert Property.objects.annotate(offers=Count("listings")).filter(offers=3).exists()

    falling = Listing.objects.get(source__slug="demo-fonte-1", external_id="demo-001")
    history = list(falling.price_history.order_by("captured_at"))
    assert len(history) == 3
    assert history[0].price > history[1].price > history[2].price == falling.price
    assert history[0].captured_at < history[1].captured_at < history[2].captured_at

    client = APIClient()
    response = client.get("/api/properties/")
    assert response.status_code == 200
    assert response.data["count"] == 29  # Fully inactive property excluded.
    assert response.data["next"] is not None
    response = client.get("/api/properties/", {"city": "Salvador", "transaction_type": "sale"})
    assert response.status_code == 200
    assert response.data["count"] == 3
    assert all(item["city"] == "Salvador" for item in response.data["results"])
    detail = client.get(f"/api/properties/{falling.property_id}/")
    assert detail.status_code == 200
    assert detail.data["listings"][0]["title"].startswith("[DEMO]")


@pytest.mark.django_db
def test_reseeding_preserves_records_and_manual_edits_without_extra_history():
    unrelated = SourceFactory.create(slug="unrelated")
    call_command("seed_demo", stdout=StringIO())
    listing = Listing.objects.first()
    Listing.objects.filter(pk=listing.pk).update(title="Edited during testing", is_active=False)
    counts = (Source.objects.count(), Property.objects.count(), Listing.objects.count(), ListingPriceHistory.objects.count())

    call_command("seed_demo", stdout=StringIO())

    assert (Source.objects.count(), Property.objects.count(), Listing.objects.count(), ListingPriceHistory.objects.count()) == counts
    listing.refresh_from_db()
    assert listing.title == "Edited during testing"
    assert listing.is_active is False
    assert Source.objects.filter(pk=unrelated.pk).exists()
