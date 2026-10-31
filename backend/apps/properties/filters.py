from decimal import Decimal
from django.db.models import F, Q
from rest_framework import serializers


class SearchParameters(serializers.Serializer):
    city = serializers.CharField(required=False, max_length=120)
    state = serializers.CharField(required=False, max_length=2)
    neighborhood = serializers.CharField(required=False, max_length=120)
    location = serializers.CharField(required=False, max_length=240)
    q = serializers.CharField(required=False, max_length=300)
    transaction_type = serializers.ChoiceField(choices=["sale", "rent"], required=False)
    property_type = serializers.ChoiceField(choices=["apartment", "house", "land", "commercial", "other"], required=False)
    min_price = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal("0"), required=False)
    max_price = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal("0"), required=False)
    min_area = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0"), required=False)
    max_area = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0"), required=False)
    bedrooms = serializers.IntegerField(min_value=0, required=False)
    bathrooms = serializers.IntegerField(min_value=0, required=False)
    parking_spaces = serializers.IntegerField(min_value=0, required=False)
    ordering = serializers.ChoiceField(choices=["city", "-city", "updated_at", "-updated_at", "price", "-price", "area", "-area", "price_per_m2", "-price_per_m2", "price_drop", "-price_drop"], required=False)

    def validate(self, values):
        for field in ("price", "area"):
            low, high = values.get(f"min_{field}"), values.get(f"max_{field}")
            if low is not None and high is not None and low > high:
                raise serializers.ValidationError({f"max_{field}": "Deve ser maior ou igual ao mínimo."})
        return values


def offer_constraint(params):
    conditions = Q(is_active=True, source__is_published=True)
    for field, lookup in {
        "city": "city__icontains", "state": "state__iexact", "neighborhood": "neighborhood__icontains",
        "transaction_type": "transaction_type", "property_type": "property_type",
        "min_price": "price__gte", "max_price": "price__lte", "min_area": "area__gte", "max_area": "area__lte",
        "bedrooms": "bedrooms__gte", "bathrooms": "bathrooms__gte", "parking_spaces": "parking_spaces__gte",
    }.items():
        if field in params:
            conditions &= Q(**{lookup: params[field]})
    if location := params.get("location"):
        conditions &= Q(city__icontains=location) | Q(neighborhood__icontains=location) | Q(state__iexact=location)
    types = {"apartamento": "apartment", "casa": "house", "terreno": "land", "comercial": "commercial"}
    for term in params.get("q", "").split():
        if term.lower() in {"em", "com", "de", "e"}:
            continue
        text = Q(title__icontains=term) | Q(description__icontains=term) | Q(city__icontains=term) | Q(neighborhood__icontains=term)
        if term.lower() in types:
            text |= Q(property_type=types[term.lower()])
        conditions &= text
    return conditions


def ordering_expression(value):
    descending = value.startswith("-")
    name = {"price": "min_price", "area": "matching_area", "price_per_m2": "price_per_m2", "price_drop": "price_drop_percent", "updated_at": "last_seen", "city": "city"}.get(value.lstrip("-"), "last_seen")
    return F(name).desc(nulls_last=True) if descending else F(name).asc(nulls_last=True)
