from datetime import timedelta

from django.db import migrations, models


def validate_window(apps, schema_editor):
    Redirect = apps.get_model("analytics", "RedirectEvent")
    outside = (models.Q(created_at__lt=models.F("exposure__created_at")) |
               models.Q(created_at__gte=models.F("exposure__created_at") + timedelta(minutes=30)))
    Redirect.objects.using(schema_editor.connection.alias).filter(
        exposure__isnull=False).filter(outside).update(exposure=None, was_attributed=False)


class Migration(migrations.Migration):
    dependencies = [("analytics", "0005_journeyevent_unique_exposure_per_opening_listing")]
    operations = [migrations.RunPython(validate_window, migrations.RunPython.noop)]
