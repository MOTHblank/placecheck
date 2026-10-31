from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from .manual import ManualProvider


def build_provider(source):
    """Resolve o provider de uma fonte sem acoplar tarefas ao provider concreto."""
    if source.provider_type == source.ProviderType.MANUAL:
        records_by_source = getattr(settings, "MANUAL_PROVIDER_RECORDS", {})
        return ManualProvider(records_by_source.get(source.slug, {}))
    raise ImproperlyConfigured(
        f"Nenhum provider configurado para o tipo {source.provider_type!r}."
    )
