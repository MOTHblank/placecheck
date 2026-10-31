from apps.analytics.models import RedirectEvent


class RedirectEventFactory:
    @staticmethod
    def create(**kwargs):
        from apps.listings.tests.factories import ListingFactory

        values = {
            "listing": kwargs.pop("listing", None) or ListingFactory.create(),
        }
        values.update(kwargs)
        return RedirectEvent.objects.create(**values)
