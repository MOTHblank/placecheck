from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.sources.models import Source
from apps.sources.providers.imoveis_leilao_brasil import SOURCE_SLUG
from apps.sources.providers.registry import configured_ilb_provider


class Command(BaseCommand):
    help = "Configura a Fonte experimental ILB no stack interno; não coleta dados."

    def handle(self, *args, **options):
        if not settings.DEBUG or not settings.ILB_PILOT_ENABLED:
            raise CommandError("Habilite explicitamente o piloto em um stack local isolado.")
        try:
            provider = configured_ilb_provider()
        except ValueError as error:
            raise CommandError(str(error)) from None
        scope = provider.collection_scope
        existing = Source.objects.filter(slug=SOURCE_SLUG).first()
        if existing and existing.collection_scope != scope:
            raise CommandError("Recorte existente diferente; use outro stack isolado, sem misturar inventários.")
        source, _ = Source.objects.update_or_create(slug=SOURCE_SLUG, defaults={
            "name": "Imóveis Leilão Brasil — piloto CAIXA", "provider_type": Source.ProviderType.API,
            "base_url": "https://www.imoveisleilaobrasil.com.br/api",
            "collection_scope": scope,
            "attribution_text": "Dados públicos da CAIXA via Imóveis Leilão Brasil (Spartan TI). Confirme condições no edital oficial.",
            "is_active": True, "is_published": True, "is_demo": False, "rate_limit_per_minute": 30,
            "can_store_description": False, "can_store_images": False,
            "can_retain_price_history": settings.ILB_PILOT_PRICE_HISTORY,
        })
        history = "Histórico habilitado no escopo interno aprovado." if source.can_retain_price_history else "Sem histórico."
        self.stdout.write(f"Fonte {source.pk}: {scope}; "
                          f"até {settings.ILB_PILOT_LIMIT} itens por mercado, captura parcial, cache diário. {history}")
