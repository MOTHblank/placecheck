import json

from django.core.management.base import BaseCommand

from apps.analytics.inventory import inventory_report


class Command(BaseCommand):
    help = "Estoque atual e sincronização por Fonte; restrito à equipe com acesso ao ambiente."

    def add_arguments(self, parser):
        parser.add_argument("--source", type=int)
        parser.add_argument("--city")
        parser.add_argument("--state")
        parser.add_argument("--transaction", choices=["sale", "rent"])
        parser.add_argument("--timezone", default="America/Bahia")

    def handle(self, *args, **options):
        result = inventory_report(source=options["source"], city=options["city"], state=options["state"],
                                  transaction_type=options["transaction"], timezone_name=options["timezone"])
        self.stdout.write(json.dumps(result, ensure_ascii=False))
