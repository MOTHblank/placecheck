from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.sources.models import Source
from apps.sources.providers.imoveis_leilao_brasil import SOURCE_SLUG, ImoveisLeilaoBrasilProvider


class Command(BaseCommand):
    help = "Configura a Fonte experimental ILB no stack interno; não coleta dados."

    def handle(self, *args, **options):
        if not settings.DEBUG or not settings.ILB_PILOT_ENABLED:
            raise CommandError("Habilite explicitamente o piloto em um stack local isolado.")
        try:
            ImoveisLeilaoBrasilProvider(uf=settings.ILB_PILOT_UF, city=settings.ILB_PILOT_CITY,
                                       limit=settings.ILB_PILOT_LIMIT)
        except ValueError as error:
            raise CommandError(str(error)) from None
        scope = f"{settings.ILB_PILOT_UF.upper()}:{settings.ILB_PILOT_CITY}"
        existing = Source.objects.filter(slug=SOURCE_SLUG).first()
        if existing and existing.collection_scope != scope:
            raise CommandError("Recorte existente diferente; use outro stack isolado, sem misturar inventários.")
        source, _ = Source.objects.update_or_create(slug=SOURCE_SLUG, defaults={
            "name": "Imóveis Leilão Brasil — piloto CAIXA", "provider_type": Source.ProviderType.API,
            "base_url": "https://www.imoveisleilaobrasil.com.br/api",
            "collection_scope": scope,
            "attribution_text": "Dados públicos da CAIXA via Imóveis Leilão Brasil (Spartan TI). Confirme condições no edital oficial.",
            "is_active": True, "is_published": True, "is_demo": False, "rate_limit_per_minute": 30,
            "can_store_description": False, "can_store_images": False, "can_retain_price_history": False,
        })
        self.stdout.write(f"Fonte {source.pk}: {settings.ILB_PILOT_UF}/{settings.ILB_PILOT_CITY}; "
                          f"até {settings.ILB_PILOT_LIMIT} itens, captura parcial, cache diário. Sem histórico.")
