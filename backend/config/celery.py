import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("placecheck")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
app.conf.beat_schedule = {
    "sync-active-sources-every-15-minutes": {
        "task": "apps.ingestion.tasks.sync_active_sources",
        "schedule": 900.0,
    },
}
