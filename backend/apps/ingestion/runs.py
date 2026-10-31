from uuid import uuid4

from django.db import transaction
from django.utils import timezone

from apps.sources.models import Source
from .models import SyncRun


@transaction.atomic
def start_run(source, task_id=None):
    Source.objects.select_for_update().get(pk=source.pk)
    task_id = task_id or str(uuid4())
    existing = SyncRun.objects.filter(task_id=task_id).first()
    if existing:
        return existing
    source.sync_runs.filter(status__in=["discovering", "running"]).update(
        status="superseded", finished_at=timezone.now(),
    )
    return SyncRun.objects.create(source=source, task_id=task_id)


def current_run(source, run_id):
    # Caller holds the source lock through writing and reconciliation.
    run = source.sync_runs.order_by("-id").first()
    return run if run and run.pk == run_id and run.status in ("discovering", "running") else None


@transaction.atomic
def record_discovery(source, run_id, references, complete):
    Source.objects.select_for_update().get(pk=source.pk)
    run = current_run(source, run_id)
    if not run:
        return False
    run.expected_count = len(references)
    run.is_complete = complete
    run.status = "running"
    run.save(update_fields=["expected_count", "is_complete", "status"])
    return True


def fail_run(run_id, error):
    # Record the exception class only: payloads/configuration may contain secrets.
    SyncRun.objects.filter(pk=run_id, status__in=["discovering", "running"]).update(
        status="failed", failure=type(error).__name__, finished_at=timezone.now(),
    )
