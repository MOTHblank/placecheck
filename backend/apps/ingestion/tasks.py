import logging
from typing import Any

from celery import chord, chain, shared_task
from django.core.cache import cache
from django.db import DatabaseError

from apps.ingestion.exceptions import ProviderTemporaryError, SourceRateLimitExceeded
from apps.ingestion.services import persist_listing, reconcile_source_listings
from apps.sources.models import Source
from apps.sources.normalizers import normalize_listing
from apps.sources.providers.registry import build_provider

logger = logging.getLogger(__name__)


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


@shared_task(bind=True, autoretry_for=(ProviderTemporaryError,), retry_backoff=True, max_retries=3)
def sync_source(self, source_id: int) -> int:
    """Descobre referências e agenda o pipeline completo da fonte."""
    source = _source_or_raise(source_id)
    provider = build_provider(source)
    references = list(provider.discover())
    logger.info("Source %s descobriu %s referências", source.slug, len(references))
    workflows = [
        chain(
            fetch_listing.s(source_id, reference),
            process_listing.s(source_id=source_id),
        )
        for reference in references
    ]
    if workflows:
        chord(workflows)(reconcile_source.s(source_id=source_id))
    else:
        reconcile_source.delay([], source_id=source_id)
    return len(references)


@shared_task(
    bind=True,
    autoretry_for=(ProviderTemporaryError, SourceRateLimitExceeded, DatabaseError),
    retry_backoff=True,
    max_retries=3,
    soft_time_limit=30,
    time_limit=45,
)
def fetch_listing(self, source_id: int, reference: str) -> Any:
    """Busca um payload para a etapa de parsing e normalização."""
    source = _source_or_raise(source_id)
    _check_source_rate_limit(source)
    try:
        payload = build_provider(source).fetch(reference)
    except (TimeoutError, ConnectionError) as error:
        logger.warning("Falha transitória ao buscar %s/%s", source.slug, reference)
        raise ProviderTemporaryError(str(error)) from error
    return payload


@shared_task(
    bind=True,
    autoretry_for=(ProviderTemporaryError, DatabaseError),
    retry_backoff=True,
    max_retries=3,
    soft_time_limit=30,
    time_limit=45,
)
def process_listing(self, payload: Any, source_id: int) -> str:
    """Faz parse, normaliza e persiste fora do provider."""
    source = _source_or_raise(source_id)
    try:
        raw_listing = build_provider(source).parse(payload)
        normalized_listing = normalize_listing(raw_listing)
        listing = persist_listing(source, normalized_listing)
    except (ValueError, KeyError) as error:
        logger.exception("Payload inválido para source=%s", source.slug)
        raise ProviderTemporaryError(str(error)) from error
    logger.info("Listing %s processado para source=%s", listing.external_id, source.slug)
    return listing.external_id


@shared_task
def reconcile_source(results: list[str], source_id: int) -> int:
    """Finaliza a sincronização após todos os anúncios serem processados."""
    source = _source_or_raise(source_id)
    deactivated = reconcile_source_listings(source, results)
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
