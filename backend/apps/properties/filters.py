from django.db.models import Q


def filter_properties(queryset, params):
    if city := params.get("city"):
        queryset = queryset.filter(city__icontains=city)
    if state := params.get("state"):
        queryset = queryset.filter(state__iexact=state)
    if neighborhood := params.get("neighborhood"):
        queryset = queryset.filter(neighborhood__icontains=neighborhood)
    if property_type := params.get("property_type"):
        queryset = queryset.filter(property_type=property_type)
    if transaction_type := params.get("transaction_type"):
        queryset = queryset.filter(listings__transaction_type=transaction_type, listings__is_active=True)
    if bedrooms := params.get("bedrooms"):
        queryset = queryset.filter(listings__bedrooms__gte=bedrooms, listings__is_active=True)
    if min_price := params.get("min_price"):
        queryset = queryset.filter(listings__price__gte=min_price, listings__is_active=True)
    if max_price := params.get("max_price"):
        queryset = queryset.filter(listings__price__lte=max_price, listings__is_active=True)
    return queryset


def ordering_expression(value):
    allowed = {
        "city": "city",
        "-city": "-city",
        "updated_at": "updated_at",
        "-updated_at": "-updated_at",
        "price": "min_price",
        "-price": "-min_price",
    }
    return allowed.get(value, "-updated_at")
