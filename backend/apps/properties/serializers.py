from rest_framework import serializers
from django.utils import timezone

from apps.listings.models import Listing

from .models import Property


class PriceHistorySerializer(serializers.Serializer):
    price = serializers.DecimalField(max_digits=14, decimal_places=2)
    captured_at = serializers.DateTimeField()


class ListingOfferSerializer(serializers.ModelSerializer):
    source_url = serializers.URLField(source="source.base_url", read_only=True)
    attribution_text = serializers.CharField(source="source.attribution_text", read_only=True)
    is_demo = serializers.BooleanField(source="source.is_demo", read_only=True)
    source = serializers.CharField(source="source.name", read_only=True)
    previous_price = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True, allow_null=True)
    initial_price = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True, allow_null=True)
    lowest_price = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True, allow_null=True)
    highest_price = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True, allow_null=True)
    price_per_m2 = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True, allow_null=True)
    price_drop_percent = serializers.FloatField(read_only=True, allow_null=True)
    days_on_market = serializers.SerializerMethodField()
    price_history = PriceHistorySerializer(many=True, read_only=True)

    def get_days_on_market(self, obj):
        return max(0, (timezone.now() - obj.first_seen_at).days)

    class Meta:
        model = Listing
        fields = (
            "id",
            "source",
            "source_url", "attribution_text", "sale_method", "price_kind", "source_inventory_date",
            "is_demo",
            "title",
            "description",
            "transaction_type",
            "price",
            "condominium_fee",
            "iptu",
            "area",
            "bedrooms",
            "bathrooms",
            "suites",
            "parking_spaces",
            "url",
            "published_at",
            "last_seen_at",
            "previous_price", "initial_price", "lowest_price", "highest_price",
            "price_per_m2", "price_drop_percent", "days_on_market", "price_history",
        )


class PropertyListSerializer(serializers.ModelSerializer):
    has_special_sale = serializers.BooleanField(read_only=True)
    has_demo_offers = serializers.BooleanField(read_only=True)
    listing_count = serializers.IntegerField(read_only=True)
    min_price = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True, allow_null=True)
    price_per_m2 = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True, allow_null=True)
    price_drop_percent = serializers.FloatField(read_only=True, allow_null=True)

    class Meta:
        model = Property
        fields = (
            "id",
            "property_type",
            "city",
            "state",
            "neighborhood",
            "area",
            "bedrooms",
            "bathrooms",
            "suites",
            "parking_spaces",
            "listing_count",
            "has_demo_offers",
            "has_special_sale",
            "min_price",
            "price_per_m2", "price_drop_percent",
        )


class PropertyDetailSerializer(PropertyListSerializer):
    listings = ListingOfferSerializer(source="matching_listings", many=True, read_only=True)

    class Meta(PropertyListSerializer.Meta):
        fields = PropertyListSerializer.Meta.fields + ("latitude", "longitude", "listings")
