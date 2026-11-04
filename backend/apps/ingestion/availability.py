from django.db import transaction
from django.utils import timezone

from apps.listings.models import Listing
from apps.properties.services import refresh_property
from apps.sources.models import Source
from .models import ListingAvailabilityCheck


@transaction.atomic
def record_availability_check(source, listing_id, *, last_seen_at, started_at, status, failure=""):
    current = Source.objects.select_for_update().get(pk=source.pk)
    if (not current.is_active or not current.is_published or current.is_demo
            or current.updated_at != source.updated_at or current.collection_scope != source.collection_scope):
        return False
    listing = Listing.objects.select_for_update(no_key=True).filter(
        pk=listing_id, source=current, is_active=True, last_seen_at=last_seen_at,
    ).first()
    if not listing:
        return False
    previous = ListingAvailabilityCheck.objects.filter(listing=listing).first()
    if previous and previous.checked_at >= started_at:
        return False
    ListingAvailabilityCheck.objects.update_or_create(listing=listing, defaults={
        "checked_at": timezone.now(), "status": status, "failure": failure,
    })
    if status == ListingAvailabilityCheck.Status.MISSING:
        Listing.objects.filter(pk=listing.pk).update(is_active=False, updated_at=timezone.now())
        if listing.property_id:
            refresh_property(listing.property_id)
    return True
