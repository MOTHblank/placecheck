from django.db import models

from apps.sources.models import Source


class SyncRun(models.Model):
    class Status(models.TextChoices):
        DISCOVERING = "discovering", "Descobrindo"
        RUNNING = "running", "Processando"
        SUCCEEDED = "succeeded", "Completa"
        PARTIAL = "partial", "Parcial"
        FAILED = "failed", "Falhou"
        SUPERSEDED = "superseded", "Substituída"

    source = models.ForeignKey(Source, on_delete=models.CASCADE, related_name="sync_runs")
    task_id = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DISCOVERING)
    is_complete = models.BooleanField(default=False)
    expected_count = models.PositiveIntegerField(default=0)
    processed_ids = models.JSONField(default=list)
    processed_count = models.PositiveIntegerField(default=0)
    deactivated_count = models.PositiveIntegerField(default=0)
    failure = models.CharField(max_length=255, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-id"]
