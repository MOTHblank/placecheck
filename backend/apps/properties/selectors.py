from decimal import Decimal

from django.db.models import Case, Count, DecimalField, Exists, ExpressionWrapper, F, FloatField, Max, Min, OuterRef, Prefetch, Subquery, Value, When
from django.db.models.functions import Cast, Greatest, NullIf

from apps.listings.models import Listing, ListingPriceHistory
from .filters import offer_constraint, ordering_expression
from .models import Property


def matching_offers(params):
    history = ListingPriceHistory.objects.filter(listing_id=OuterRef("pk"))
    money = DecimalField(max_digits=18, decimal_places=2)
    return Listing.objects.filter(offer_constraint(params)).select_related("source").annotate(
        previous_price=Subquery(history.order_by("-captured_at", "-id").values("price")[1:2]),
        initial_price=Subquery(history.order_by("captured_at", "id").values("price")[:1]),
        lowest_price=Subquery(history.order_by("price").values("price")[:1]),
        highest_price=Subquery(history.order_by("-price").values("price")[:1]),
        price_per_m2=ExpressionWrapper(F("price") / NullIf(F("area"), Value(Decimal("0"))), output_field=money),
    ).annotate(
        price_drop_percent=Case(
            When(initial_price__gt=0, price__isnull=False, then=Greatest(Value(0.0), (Cast(F("initial_price"), FloatField()) - Cast(F("price"), FloatField())) * 100.0 / NullIf(Cast(F("initial_price"), FloatField()), Value(0.0)))),
            default=None,
            output_field=FloatField(),
        ),
    )


def property_search(params, include_offers=False):
    offers = matching_offers(params)
    grouped = offers.filter(property_id=OuterRef("pk")).order_by().values("property_id")
    summary = grouped.annotate(
        total=Count("pk"), price=Min("price"), area_value=Max("area"),
        unit_price=Min("price_per_m2"), drop=Max("price_drop_percent"), seen=Max("last_seen_at"),
    )
    queryset = Property.objects.filter(Exists(grouped)).annotate(
        listing_count=Subquery(summary.values("total")[:1]),
        min_price=Subquery(summary.values("price")[:1]),
        matching_area=Subquery(summary.values("area_value")[:1]),
        price_per_m2=Subquery(summary.values("unit_price")[:1]),
        price_drop_percent=Subquery(summary.values("drop")[:1]),
        last_seen=Subquery(summary.values("seen")[:1]),
        has_demo_offers=Exists(grouped.filter(source__is_demo=True)),
    ).order_by(ordering_expression(params.get("ordering", "-updated_at")), "id")
    if include_offers:
        queryset = queryset.prefetch_related(Prefetch("listings", queryset=offers.order_by(F("price").asc(nulls_last=True), "id").prefetch_related("price_history"), to_attr="matching_listings"))
    return queryset
