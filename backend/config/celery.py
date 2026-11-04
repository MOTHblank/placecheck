import os

from celery import Celery
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("placecheck")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
app.conf.beat_schedule = {
    "purge-expired-analytics-hourly": {
        "task": "apps.analytics.tasks.purge_expired_analytics",
        "schedule": 3600,
    },
    "sync-active-sources-every-15-minutes": {
        "task": "apps.ingestion.tasks.sync_active_sources",
        "schedule": settings.CELERY_SYNC_INTERVAL_SECONDS,
    },
    "check-ilb-availability-every-15-minutes": {
        "task": "apps.sources.tasks.queue_ilb_availability_checks",
        "schedule": settings.CELERY_SYNC_INTERVAL_SECONDS,
    },
}
