import logging
from typing import Any

from celery import Task, chord, chain, shared_task
from django.core.cache import cache
from django.db import DatabaseError

from apps.ingestion.exceptions import ProviderTemporaryError, SourceRateLimitExceeded
from apps.ingestion.services import persist_listing, reconcile_source_listings
from apps.sources.models import Source
from apps.sources.normalizers import normalize_listing
from apps.sources.providers.registry import build_provider
from apps.ingestion.models import SyncRun
from apps.ingestion.runs import fail_run, record_discovery, start_run

logger = logging.getLogger(__name__)


class IngestionTask(Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        run_id = kwargs.get("run_id")
        if run_id is None:
            run_id = SyncRun.objects.filter(task_id=task_id).values_list("pk", flat=True).first()
        if run_id:
            fail_run(run_id, exc)
        logger.error("Ingestion task failed: task=%s run=%s error=%s", task_id, run_id, type(exc).__name__)


def _source_or_raise(source_id: int) -> Source:
    try:
        return Source.objects.get(id=source_id, is_active=True)
    except Source.DoesNotExist as error:
        raise ValueError(f"Source ativa não encontrada: {source_id}") from error


def _check_source_rate_limit(source: Source) -> None:
    key = f"placecheck:source-rate:{source.pk}"
    try:
        if cache.add(key, 1, timeout=60):
            current = 1
        else:
            current = cache.incr(key)
    except ValueError:
        current = 1
        cache.set(key, current, timeout=60)
    if current > source.rate_limit_per_minute:
        raise SourceRateLimitExceeded(f"Rate limit atingido para source={source.pk}")


@shared_task(base=IngestionTask, bind=True, autoretry_for=(ProviderTemporaryError, SourceRateLimitExceeded, DatabaseError), retry_backoff=True, max_retries=3, soft_time_limit=30, time_limit=45)
def sync_source(self, source_id: int) -> int:
    """Descobre referências e agenda o pipeline completo da fonte."""
    source = _source_or_raise(source_id)
    run = start_run(source, self.request.id)
    if run.status not in ("discovering", "running"):
        return 0
    try:
        _check_source_rate_limit(source)
    except SourceRateLimitExceeded as error:
        raise self.retry(exc=error, countdown=60, max_retries=None)
    provider = build_provider(source)
    try:
        references = list(dict.fromkeys(provider.discover()))
    except (TimeoutError, ConnectionError) as error:
        raise ProviderTemporaryError() from error
    if not all(isinstance(reference, str) and reference.strip() for reference in references):
        raise ValueError("Referência inválida no inventário.")
    if not record_discovery(source, run.pk, references, provider.is_complete_snapshot):
        return 0
    logger.info("Source %s descobriu %s referências", source.slug, len(references))
    workflows = [
        chain(
            fetch_listing.s(source_id, reference, run_id=run.pk),
            process_listing.s(source_id=source_id, run_id=run.pk),
        )
        for reference in references
    ]
    if workflows:
        chord(workflows)(reconcile_source.s(source_id=source_id, run_id=run.pk))
    else:
        reconcile_source.delay([], source_id=source_id, run_id=run.pk)
    return len(references)


@shared_task(
    base=IngestionTask,
    bind=True,
    autoretry_for=(ProviderTemporaryError, SourceRateLimitExceeded, DatabaseError),
    retry_backoff=True,
    max_retries=3,
    soft_time_limit=30,
    time_limit=45,
)
def fetch_listing(self, source_id: int, reference: str, *, run_id=None) -> Any:
    """Busca um payload para a etapa de parsing e normalização."""
    source = _source_or_raise(source_id)
    if run_id and not source.sync_runs.filter(pk=run_id, status="running").exists():
        return None
    try:
        _check_source_rate_limit(source)
    except SourceRateLimitExceeded as error:
        if not self.request.id:
            raise
        raise self.retry(exc=error, countdown=60, max_retries=None)
    try:
        payload = build_provider(source).fetch(reference)
    except (TimeoutError, ConnectionError) as error:
        logger.warning("Falha transitória ao buscar %s/%s", source.slug, reference)
        raise ProviderTemporaryError(str(error)) from error
    return payload


@shared_task(
    base=IngestionTask,
    bind=True,
    autoretry_for=(ProviderTemporaryError, DatabaseError),
    retry_backoff=True,
    max_retries=3,
    soft_time_limit=30,
    time_limit=45,
)
def process_listing(self, payload: Any, source_id: int, *, run_id=None) -> str | None:
    """Faz parse, normaliza e persiste fora do provider."""
    source = _source_or_raise(source_id)
    if run_id and not source.sync_runs.filter(pk=run_id, status="running").exists():
        return None
    raw_listing = build_provider(source).parse(payload)
    normalized_listing = normalize_listing(raw_listing)
    listing = persist_listing(source, normalized_listing, run_id=run_id)
    if listing is None:
        return None
    logger.info("Listing %s processado para source=%s", listing.external_id, source.slug)
    return listing.external_id


@shared_task(base=IngestionTask, bind=True, autoretry_for=(DatabaseError,), retry_backoff=True, max_retries=3, soft_time_limit=30, time_limit=45)
def reconcile_source(self, results: list[str], source_id: int, *, run_id=None) -> int:
    """Finaliza a sincronização após todos os anúncios serem processados."""
    source = _source_or_raise(source_id)
    if run_id is None:
        raise ValueError("Reconciliação assíncrona exige execução identificada.")
    deactivated = reconcile_source_listings(source, results, run_id=run_id)
    logger.info(
        "Source %s reconciliada: %s processados, %s desativados",
        source.slug,
        len(results),
        deactivated,
    )
    return deactivated


@shared_task
def sync_active_sources() -> int:
    """Task chamada pelo Celery Beat para disparar fontes ativas."""
    source_ids = list(Source.objects.filter(is_active=True).values_list("id", flat=True))
    for source_id in source_ids:
        sync_source.delay(source_id)
    logger.info("%s sources ativas enfileiradas", len(source_ids))
    return len(source_ids)
