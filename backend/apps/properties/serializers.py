from rest_framework import serializers
from django.utils import timezone

from apps.listings.models import Listing

from .models import Property


class ListingOfferSerializer(serializers.ModelSerializer):
    source = serializers.CharField(source="source.name", read_only=True)
    previous_price = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True, allow_null=True)
    initial_price = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True, allow_null=True)
    lowest_price = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True, allow_null=True)
    highest_price = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True, allow_null=True)
    price_per_m2 = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True, allow_null=True)
    price_drop_percent = serializers.FloatField(read_only=True, allow_null=True)
    days_on_market = serializers.SerializerMethodField()
    price_history = serializers.SerializerMethodField()

    def get_days_on_market(self, obj):
        return max(0, (timezone.now() - obj.first_seen_at).days)

    def get_price_history(self, obj):
        return [{"price": str(item.price), "captured_at": item.captured_at.isoformat()} for item in obj.price_history.all()]

    class Meta:
        model = Listing
        fields = (
            "id",
            "source",
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
            "min_price",
            "price_per_m2", "price_drop_percent",
        )


class PropertyDetailSerializer(PropertyListSerializer):
    listings = serializers.SerializerMethodField()

    class Meta(PropertyListSerializer.Meta):
        fields = PropertyListSerializer.Meta.fields + ("latitude", "longitude", "listings")

    def get_listings(self, obj):
        listings = obj.matching_listings
        return ListingOfferSerializer(listings, many=True).data
