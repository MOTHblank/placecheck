import os

from celery import Celery
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("placecheck")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
app.conf.beat_schedule = {
    "sync-active-sources-every-15-minutes": {
        "task": "apps.ingestion.tasks.sync_active_sources",
        "schedule": settings.CELERY_SYNC_INTERVAL_SECONDS,
    },
}
