from uuid import uuid4

import pytest
from django.conf import settings

from config.celery import app


def test_configured_redis_broker_round_trips_a_json_message():
    if not settings.CELERY_BROKER_URL.startswith(("redis://", "rediss://")):
        pytest.skip("Requires the configured Redis broker, not an in-memory substitute.")
    queue_name = f"placecheck-broker-regression-{uuid4().hex}"
    payload = {"check": "redis-round-trip", "value": 42}
    with app.connection_for_write() as connection:
        with connection.SimpleQueue(queue_name) as queue:
            try:
                queue.put(payload, serializer="json")
                message = queue.get(block=True, timeout=5)
                assert message.payload == payload
                message.ack()
            finally:
                queue.queue.delete()
