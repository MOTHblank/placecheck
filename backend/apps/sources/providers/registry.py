from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
import json
from pathlib import Path

from .manual import ManualProvider
from .imoveis_leilao_brasil import SOURCE_SLUG, ImoveisLeilaoBrasilMarketsProvider, ImoveisLeilaoBrasilProvider
from apps.ingestion.limits import check_source_rate_limit


def configured_ilb_provider(source=None):
    configured = getattr(settings, "ILB_PILOT_MARKETS", "")
    if not isinstance(configured, str):
        raise ValueError("ILB_PILOT_MARKETS deve ser uma lista textual UF:cidade.")
    if configured.strip():
        entries = [entry.strip().split(":") for entry in configured.split(",")]
        if not 1 <= len(entries) <= 2 or any(len(entry) != 2 for entry in entries):
            raise ValueError("Configure de um a dois mercados ILB como UF:cidade.")
        providers = [ImoveisLeilaoBrasilProvider(uf=uf.strip(), city=city.strip(), limit=settings.ILB_PILOT_LIMIT)
                     for uf, city in entries]
    else:
        providers = [ImoveisLeilaoBrasilProvider(uf=settings.ILB_PILOT_UF, city=settings.ILB_PILOT_CITY,
                                               limit=settings.ILB_PILOT_LIMIT)]
    restricted_scope = len(providers) > 1 or settings.ILB_PILOT_PRICE_HISTORY or (
        source is not None and source.can_retain_price_history
    )
    if restricted_scope and (
        settings.ILB_PILOT_LIMIT > 2
        or any(provider.collection_scope not in {"BA:salvador", "SP:campinas"} for provider in providers)
    ):
        raise ValueError("Piloto conjunto e histórico aprovados somente para Salvador/BA e Campinas/SP, até dois itens por mercado.")
    if source and source.rate_limit_per_minute < len(providers):
        raise ValueError("Rate limit da Fonte deve comportar os mercados da descoberta.")
    provider = providers[0] if len(providers) == 1 else ImoveisLeilaoBrasilMarketsProvider(providers,
        additional_request_budget=(lambda: check_source_rate_limit(source)) if source else None)
    if len(provider.collection_scope) > 150:
        raise ValueError("Recorte ILB excede o tamanho permitido de collection_scope.")
    return provider


def build_provider(source):
    """Resolve o provider de uma fonte sem acoplar tarefas ao provider concreto."""
    if source.slug == SOURCE_SLUG:
        if not settings.DEBUG or not settings.ILB_PILOT_ENABLED or source.provider_type != source.ProviderType.API:
            raise ImproperlyConfigured("Piloto ILB disponível somente no ambiente interno explicitamente habilitado.")
        try:
            provider = configured_ilb_provider(source)
        except ValueError as error:
            raise ImproperlyConfigured(str(error)) from error
        if source.collection_scope != provider.collection_scope:
            raise ImproperlyConfigured("Recorte ILB mudou; use outro stack isolado para o novo recorte.")
        return provider
    if source.provider_type == source.ProviderType.MANUAL:
        records_by_source = getattr(settings, "MANUAL_PROVIDER_RECORDS", {})
        records_file = getattr(settings, "MANUAL_PROVIDER_RECORDS_FILE", "")
        if records_file:
            try:
                records_by_source = json.loads(Path(records_file).read_text(encoding="utf-8"))
            except (OSError, ValueError) as error:
                raise ImproperlyConfigured("Arquivo de inventário manual ausente ou inválido.") from error
        if not isinstance(records_by_source, dict):
            raise ImproperlyConfigured("Configuração manual deve ser um objeto de Fontes.")
        if source.slug not in records_by_source:
            raise ImproperlyConfigured(f"Inventário manual não configurado: {source.slug}")
        records = records_by_source[source.slug]
        if not isinstance(records, dict):
            raise ImproperlyConfigured("Inventário manual deve ser um objeto de referências.")
        return ManualProvider(records)
    raise ImproperlyConfigured(
        f"Nenhum provider configurado para o tipo {source.provider_type!r}."
    )
