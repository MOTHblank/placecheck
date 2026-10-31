from collections import Counter
from django.db import transaction
from .models import Property


@transaction.atomic
def refresh_property(property_id):
    """Active-offer consensus; ties use the newest nonmissing value.

    Coordinates are selected as a pair. Zero counts are valid values.
    """
    property_ = Property.objects.select_for_update(no_key=True).get(pk=property_id)
    listings = list(property_.listings.filter(is_active=True, source__is_published=True).order_by("-last_seen_at", "-id"))
    if not listings:
        return property_
    fields = ("property_type", "city", "state", "neighborhood", "area", "bedrooms", "bathrooms", "suites", "parking_spaces")
    for field in fields:
        values = [getattr(item, field) for item in listings if getattr(item, field) not in (None, "")]
        value = Counter(values).most_common(1)[0][0] if values else ("" if field in ("property_type", "city", "state", "neighborhood") else None)
        if field == "property_type" and value not in Property.PropertyType.values:
            value = Property.PropertyType.OTHER
        setattr(property_, field, value)
    coordinates = [(item.latitude, item.longitude) for item in listings if item.latitude is not None and item.longitude is not None]
    property_.latitude, property_.longitude = Counter(coordinates).most_common(1)[0][0] if coordinates else (None, None)
    property_.save()
    return property_
