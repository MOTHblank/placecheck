from django.db import models

from apps.properties.models import Property
from apps.sources.models import Source


class Listing(models.Model):
    class PriceKind(models.TextChoices):
        ASKING = "asking", "Preço pedido"
        MINIMUM = "minimum", "Valor mínimo"
        REFERENCE = "reference", "Valor informado a confirmar"

    class TransactionType(models.TextChoices):
        SALE = "sale", "Venda"
        RENT = "rent", "Aluguel"

    property = models.ForeignKey(
        Property,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="listings",
    )
    source = models.ForeignKey(Source, on_delete=models.PROTECT, related_name="listings")
    external_id = models.CharField(max_length=150)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    transaction_type = models.CharField(max_length=20, choices=TransactionType.choices)
    property_type = models.CharField(max_length=30)
    price = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    sale_method = models.CharField(max_length=30, blank=True)
    price_kind = models.CharField(max_length=12, choices=PriceKind.choices, default=PriceKind.ASKING)
    source_inventory_date = models.DateField(null=True, blank=True)
    condominium_fee = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    iptu = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    area = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    bedrooms = models.PositiveSmallIntegerField(null=True, blank=True)
    bathrooms = models.PositiveSmallIntegerField(null=True, blank=True)
    suites = models.PositiveSmallIntegerField(null=True, blank=True)
    parking_spaces = models.PositiveSmallIntegerField(null=True, blank=True)
    city = models.CharField(max_length=120)
    state = models.CharField(max_length=2)
    neighborhood = models.CharField(max_length=120, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    url = models.URLField()
    published_at = models.DateTimeField(null=True, blank=True)
    first_seen_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-last_seen_at", "-id"]
        constraints = [
            models.UniqueConstraint(fields=["source", "external_id"], name="unique_listing_source_external_id"),
        ]
        indexes = [
            models.Index(fields=["city", "state"]),
            models.Index(fields=["is_active", "transaction_type"]),
        ]

    def __str__(self):
        return self.title


class ListingPriceHistory(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="price_history")
    price = models.DecimalField(max_digits=14, decimal_places=2)
    captured_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-captured_at", "-id"]

    def __str__(self):
        return f"{self.listing} — {self.price}"
