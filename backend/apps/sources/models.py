from django.db import models, transaction
from django.core.validators import MinValueValidator


class Source(models.Model):
    class ProviderType(models.TextChoices):
        API = "api", "API"
        XML = "xml", "XML"
        CRAWLER = "crawler", "Crawler"
        MANUAL = "manual", "Manual"

    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=150, unique=True)
    provider_type = models.CharField(max_length=20, choices=ProviderType.choices)
    base_url = models.URLField(blank=True)
    attribution_text = models.CharField(max_length=200, blank=True)
    collection_scope = models.CharField(max_length=150, blank=True)
    is_active = models.BooleanField(default=True)
    is_published = models.BooleanField(default=True, help_text="Retirar publicação oculta ofertas, detalhes e redirects; pausar coleta usa is_active.")
    is_demo = models.BooleanField(default=False)
    rate_limit_per_minute = models.PositiveIntegerField(default=60, validators=[MinValueValidator(1)])
    can_store_images = models.BooleanField(default=False)
    can_store_description = models.BooleanField(default=False)
    can_retain_price_history = models.BooleanField(default=True)
    can_retain_analytics = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        constraints = [models.CheckConstraint(condition=models.Q(rate_limit_per_minute__gte=1), name="source_positive_rate_limit")]

    def __str__(self):
        return self.name

    @transaction.atomic
    def save(self, *args, **kwargs):
        previous = type(self).objects.select_for_update().filter(pk=self.pk).first() if self.pk else None
        super().save(*args, **kwargs)
        current = type(self).objects.get(pk=self.pk)
        if not current.can_store_description:
            self.listings.exclude(description="").update(description="")
        if not current.can_retain_price_history:
            from apps.listings.models import ListingPriceHistory

            ListingPriceHistory.objects.filter(listing__source=self).delete()
        if not current.can_retain_analytics:
            from apps.analytics.models import JourneyEvent, RedirectEvent

            RedirectEvent.objects.filter(source_key=self.pk).delete()
            JourneyEvent.objects.filter(source_key=self.pk).delete()
        if previous and previous.is_published != current.is_published:
            from apps.properties.services import refresh_property

            property_ids = self.listings.exclude(property_id=None).values_list("property_id", flat=True)
            for property_id in sorted(set(property_ids)):
                refresh_property(property_id)
