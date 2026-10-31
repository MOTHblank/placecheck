from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
import json
from pathlib import Path

from .manual import ManualProvider
from .imoveis_leilao_brasil import SOURCE_SLUG, ImoveisLeilaoBrasilProvider


def build_provider(source):
    """Resolve o provider de uma fonte sem acoplar tarefas ao provider concreto."""
    if source.slug == SOURCE_SLUG:
        if not settings.DEBUG or not settings.ILB_PILOT_ENABLED or source.provider_type != source.ProviderType.API:
            raise ImproperlyConfigured("Piloto ILB disponível somente no ambiente interno explicitamente habilitado.")
        if source.collection_scope != f"{settings.ILB_PILOT_UF.upper()}:{settings.ILB_PILOT_CITY}":
            raise ImproperlyConfigured("Recorte ILB mudou; use outro stack isolado para o novo recorte.")
        return ImoveisLeilaoBrasilProvider(uf=settings.ILB_PILOT_UF, city=settings.ILB_PILOT_CITY,
                                          limit=settings.ILB_PILOT_LIMIT)
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
