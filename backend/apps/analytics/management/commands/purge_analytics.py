import json
from django.core.management.base import BaseCommand
from apps.analytics.reporting import purge_events


class Command(BaseCommand):
    help = "Remove eventos e atribuições individuais com idade de pelo menos 90 dias."

    def handle(self, *args, **options):
        self.stdout.write(json.dumps(purge_events()))
