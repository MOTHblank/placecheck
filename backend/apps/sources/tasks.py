from datetime import timedelta
import logging

from celery import shared_task
from django.conf import settings
from django.core.cache import cache
from django.db import DatabaseError
from django.db.models import F, Q
from django.utils import timezone

from apps.ingestion.availability import record_availability_check
from apps.ingestion.exceptions import ProviderTemporaryError, SourceRateLimitExceeded
from apps.ingestion.limits import check_source_rate_limit
from apps.ingestion.models import ListingAvailabilityCheck
from apps.ingestion.tasks import IngestionTask
from apps.listings.models import Listing
from .models import Source
from .providers.imoveis_leilao_brasil import SOURCE_SLUG
from .providers.registry import build_provider

logger = logging.getLogger(__name__)


def _pilot_source(source_id=None):
    if not settings.DEBUG or not settings.ILB_PILOT_ENABLED:
        return None
    sources = Source.objects.filter(slug=SOURCE_SLUG, is_active=True, is_published=True, is_demo=False)
    if source_id is not None:
        sources = sources.filter(pk=source_id)
    return sources.first()


def _unchecked_listing(source, listing_id, cutoff):
    listing = Listing.objects.filter(pk=listing_id, source=source, is_active=True, last_seen_at__lt=cutoff).first()
    if not listing or ListingAvailabilityCheck.objects.filter(listing=listing, checked_at__gte=cutoff).exists():
        return None
    return listing


@shared_task(base=IngestionTask, autoretry_for=(DatabaseError,), retry_backoff=True,
             max_retries=3, soft_time_limit=30, time_limit=45)
def queue_ilb_availability_checks():
    source = _pilot_source()
    if not source:
        return 0
    build_provider(source)  # Validate local mode, provider type and immutable market scope.
    cutoff = timezone.now() - timedelta(days=1)
    ids = list(Listing.objects.filter(source=source, is_active=True, last_seen_at__lt=cutoff).filter(
        Q(availability_check__isnull=True) | Q(availability_check__checked_at__lt=cutoff),
    ).order_by(F("availability_check__checked_at").asc(nulls_first=True), "last_seen_at", "pk")
        .values_list("pk", flat=True)[:10])
    for listing_id in ids:
        check_ilb_listing_availability.delay(source.pk, listing_id)
    logger.info("ILB availability: source=%s queued=%s", source.pk, len(ids))
    return len(ids)


@shared_task(base=IngestionTask, bind=True, autoretry_for=(DatabaseError,), retry_backoff=True,
             max_retries=3, soft_time_limit=30, time_limit=45)
def check_ilb_listing_availability(self, source_id, listing_id):
    source = _pilot_source(source_id)
    if not source:
        return "skipped"
    cutoff = timezone.now() - timedelta(days=1)
    listing = _unchecked_listing(source, listing_id, cutoff)
    if not listing:
        return "skipped"
    lock_key = f"ilb:availability:{source.pk}:{listing.pk}"
    if not cache.add(lock_key, True, timeout=60):
        return "skipped"
    try:
        # Another worker or ingestion may have completed while we acquired the lock.
        source = _pilot_source(source_id)
        if not source:
            return "skipped"
        listing = _unchecked_listing(source, listing_id, cutoff)
        if not listing:
            return "skipped"
        provider = build_provider(source)
        started_at = timezone.now()
        status, failure = ListingAvailabilityCheck.Status.AVAILABLE, ""
        try:
            check_source_rate_limit(source)
        except SourceRateLimitExceeded as error:
            raise self.retry(exc=error, countdown=60, max_retries=None)
        try:
            if not provider.check_availability(listing.external_id):
                status = ListingAvailabilityCheck.Status.MISSING
        except ProviderTemporaryError as error:
            if self.request.retries < self.max_retries:
                raise self.retry(exc=error, countdown=2 ** self.request.retries)
            status, failure = ListingAvailabilityCheck.Status.FAILED, type(error).__name__
        except ValueError as error:
            status, failure = ListingAvailabilityCheck.Status.FAILED, type(error).__name__
        recorded = record_availability_check(source, listing.pk, last_seen_at=listing.last_seen_at,
            started_at=started_at, status=status, failure=failure)
        logger.log(logging.WARNING if failure else logging.INFO,
                   "ILB availability: source=%s listing=%s status=%s recorded=%s failure=%s",
                   source.pk, listing.pk, status, recorded, failure)
        return status if recorded else "stale"
    finally:
        cache.delete(lock_key)
