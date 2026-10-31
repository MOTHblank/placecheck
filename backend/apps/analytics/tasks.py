from celery import shared_task
from .reporting import purge_events


@shared_task
def purge_expired_analytics():
    return purge_events()
