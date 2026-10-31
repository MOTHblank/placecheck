from rest_framework import serializers

from apps.listings.models import Listing

from .models import Property


class ListingOfferSerializer(serializers.ModelSerializer):
    source = serializers.CharField(source="source.name", read_only=True)

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
        )


class PropertyListSerializer(serializers.ModelSerializer):
    listing_count = serializers.IntegerField(read_only=True)
    min_price = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True, allow_null=True)

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
        )


class PropertyDetailSerializer(PropertyListSerializer):
    listings = serializers.SerializerMethodField()

    class Meta(PropertyListSerializer.Meta):
        fields = PropertyListSerializer.Meta.fields + ("latitude", "longitude", "listings")

    def get_listings(self, obj):
        listings = obj.listings.filter(is_active=True).select_related("source")
        return ListingOfferSerializer(listings, many=True).data
