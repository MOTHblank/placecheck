from unittest.mock import patch

import pytest
from django.test import override_settings

from apps.ingestion.tasks import fetch_listing, process_listing, sync_active_sources, sync_source
from apps.listings.models import Listing
from apps.sources.providers import ManualProvider
from apps.sources.tests.factories import SourceFactory
from apps.sources.tests.test_provider import sample_record
from apps.ingestion.exceptions import SourceRateLimitExceeded
from django.core.cache import cache


@pytest.mark.django_db
@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
def test_sync_source_runs_fetch_and_process_pipeline():
    source = SourceFactory.create(slug="fonte-task")
    provider = ManualProvider({"manual-001": sample_record()})

    with patch("apps.ingestion.tasks.build_provider", return_value=provider):
        result = sync_source.delay(source.pk)

    assert result.get() == 1
    assert Listing.objects.filter(source=source, external_id="manual-001").count() == 1


@pytest.mark.django_db
@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
def test_beat_task_enqueues_only_active_sources():
    active = SourceFactory.create(slug="ativa")
    SourceFactory.create(slug="inativa", is_active=False)

    with patch("apps.ingestion.tasks.sync_source.delay") as enqueue:
        result = sync_active_sources.delay()

    assert result.get() == 1
    enqueue.assert_called_once_with(active.pk)


def test_tasks_define_timeouts_and_retry_policy():
    assert fetch_listing.soft_time_limit == 30
    assert fetch_listing.time_limit == 45
    assert process_listing.max_retries == 3


@pytest.mark.django_db
@override_settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}})
def test_fetch_enforces_source_specific_request_limit():
    cache.clear()
    source = SourceFactory.create(rate_limit_per_minute=2)
    provider = ManualProvider({"manual-001": sample_record()})
    with patch("apps.ingestion.tasks.build_provider", return_value=provider):
        assert fetch_listing.run(source.pk, "manual-001") == sample_record()
        assert fetch_listing.run(source.pk, "manual-001") == sample_record()
        with pytest.raises(SourceRateLimitExceeded):
            fetch_listing.run(source.pk, "manual-001")


@pytest.mark.django_db
@override_settings(CELERY_TASK_ALWAYS_EAGER=True, MANUAL_PROVIDER_RECORDS={})
def test_async_invalid_configuration_is_reported_without_inactivating_listings():
    from apps.listings.tests.factories import ListingFactory

    source = SourceFactory.create()
    listing = ListingFactory.create(source=source)
    result = sync_source.delay(source.pk)
    assert result.failed()
    assert source.sync_runs.latest("id").status == "failed"
    listing.refresh_from_db()
    assert listing.is_active
