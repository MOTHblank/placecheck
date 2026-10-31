from django.db import migrations
from django.utils import timezone


def baseline(apps, schema_editor):
    Window = apps.get_model("analytics", "MeasurementWindow")
    Event = apps.get_model("analytics", "RedirectEvent")
    alias = schema_editor.connection.alias
    Window.objects.using(alias).get_or_create(pk=1, defaults={"started_at": timezone.now()})
    # Preserve minimal legacy provenance; pre-contract traffic is outside the reporting window.
    for event in Event.objects.using(alias).select_related("listing__source").iterator():
        if event.listing_id:
            listing = event.listing
            event.listing_key = listing.pk
            event.source_key = listing.source_id
            event.source_slug = listing.source.slug
            event.source_name = listing.source.name
            event.city, event.state, event.transaction_type = listing.city, listing.state, listing.transaction_type
            event.save(using=alias, update_fields=["listing_key", "source_key", "source_slug", "source_name", "city", "state", "transaction_type"])


class Migration(migrations.Migration):
    dependencies = [("analytics", "0002_measurementwindow_remove_redirectevent_referer_and_more")]
    operations = [migrations.RunPython(baseline, migrations.RunPython.noop)]
