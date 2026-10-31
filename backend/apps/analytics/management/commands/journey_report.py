import json
from django.core.management.base import BaseCommand
from apps.analytics.reporting import journey_report


class Command(BaseCommand):
    help = "Relatório restrito de jornada/CTR; requer acesso autorizado ao ambiente."

    def add_arguments(self, parser):
        parser.add_argument("--start")
        parser.add_argument("--end")
        parser.add_argument("--timezone", default="America/Bahia")
        parser.add_argument("--source", type=int)
        parser.add_argument("--city")
        parser.add_argument("--state")
        parser.add_argument("--transaction", choices=["sale", "rent"])

    def handle(self, *args, **options):
        result = journey_report(start=options["start"], end=options["end"], timezone_name=options["timezone"],
            source=options["source"], city=options["city"], state=options["state"], transaction_type=options["transaction"])
        self.stdout.write(json.dumps(result, ensure_ascii=False))
