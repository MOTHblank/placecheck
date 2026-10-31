from django.db import models
from django.utils import timezone
from uuid import uuid4

from apps.listings.models import Listing
from apps.properties.models import Property


class EventSnapshot(models.Model):
    source_key = models.PositiveBigIntegerField(null=True, blank=True)
    source_slug = models.CharField(max_length=150, blank=True)
    source_name = models.CharField(max_length=150, blank=True)
    city = models.CharField(max_length=120, blank=True)
    state = models.CharField(max_length=2, blank=True)
    transaction_type = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False, db_index=True)

    class Meta:
        abstract = True


class JourneyEvent(EventSnapshot):
    class Kind(models.TextChoices):
        SEARCH = "search", "Busca"
        VIEW = "view", "Visualização"
        EXPOSURE = "exposure", "Exposição"

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    kind = models.CharField(max_length=10, choices=Kind.choices)
    context_id = models.UUIDField()
    property_key = models.PositiveBigIntegerField(null=True, blank=True)
    listing_key = models.PositiveBigIntegerField(null=True, blank=True)
    payload_digest = models.CharField(max_length=64)

    class Meta:
        indexes = [models.Index(fields=["kind", "created_at"]), models.Index(fields=["source_key", "created_at"])]


class MeasurementWindow(models.Model):
    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    started_at = models.DateTimeField(default=timezone.now, editable=False)
    purged_before = models.DateTimeField(null=True, blank=True, editable=False)


class RedirectEvent(EventSnapshot):
    listing = models.ForeignKey(Listing, on_delete=models.SET_NULL, null=True, blank=True, related_name="redirect_events")
    listing_key = models.PositiveBigIntegerField(null=True, blank=True)
    property = models.ForeignKey(
        Property,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="redirect_events",
    )
    exposure = models.ForeignKey(JourneyEvent, null=True, blank=True, on_delete=models.SET_NULL, related_name="redirects")
    was_attributed = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"Redirect {self.pk} em {self.created_at:%Y-%m-%d %H:%M}"
