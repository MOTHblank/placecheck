from datetime import datetime, timezone as datetime_timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.core.management.base import CommandError
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.sources.models import Source
from .models import JourneyEvent, MeasurementWindow, RedirectEvent
from .services import ATTRIBUTION_WINDOW, RETENTION


def report_zone(name):
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError):
        raise CommandError("Timezone IANA inválido.") from None


def parse_instant(value, zone):
    try:
        instant = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        raise CommandError("Data ISO inválida.") from None
    if instant.tzinfo:
        return instant.astimezone(datetime_timezone.utc)
    candidates = set()
    for fold in (0, 1):
        aware = instant.replace(tzinfo=zone, fold=fold)
        utc = aware.astimezone(datetime_timezone.utc)
        if utc.astimezone(zone).replace(tzinfo=None) == instant:
            candidates.add(utc)
    if len(candidates) != 1:
        raise CommandError("Horário local ambíguo ou inexistente; informe um offset explícito.")
    return candidates.pop()


def journey_report(*, start=None, end=None, timezone_name="America/Bahia", source=None,
                   city=None, state=None, transaction_type=None):
    zone = report_zone(timezone_name)
    now = timezone.now()
    window, _ = MeasurementWindow.objects.get_or_create(pk=1)
    available = max(window.started_at, window.purged_before or window.started_at, now - RETENTION)
    first = parse_instant(start, zone) if start else available
    last = parse_instant(end, zone) if end else now
    if first < available:
        raise CommandError(f"Período anterior aos dados disponíveis: {available.isoformat()}.")
    if first >= last or first > now:
        raise CommandError("Período vazio, invertido ou inteiramente futuro.")
    if any((city, state, transaction_type)) and not all((city, state, transaction_type)):
        raise CommandError("Mercado exige cidade, UF e modalidade juntas.")
    if state and (len(state) != 2 or transaction_type not in ("sale", "rent")):
        raise CommandError("Mercado inválido.")
    events = JourneyEvent.objects.filter(created_at__gte=first, created_at__lt=last, created_at__lte=now).filter(created_at__gt=now - RETENTION)
    redirects = RedirectEvent.objects.filter(created_at__gte=first, created_at__lt=last, created_at__lte=now).filter(created_at__gt=now - RETENTION)
    retained_events = JourneyEvent.objects.filter(created_at__gt=now - RETENTION, created_at__lte=now)
    retained_redirects = RedirectEvent.objects.filter(created_at__gt=now - RETENTION, created_at__lte=now)
    if source is not None:
        known = (Source.objects.filter(pk=source).exists() or retained_events.filter(source_key=source).exists()
                 or retained_redirects.filter(source_key=source).exists())
        if source < 1 or not known:
            raise CommandError("Fonte desconhecida.")
    unattributed = events.filter(city="", state="", transaction_type="")
    unknown_searches = unattributed.filter(kind="search").count() if source is None else None
    unknown_views = unattributed.filter(kind="view").count() if source is None else None
    if city:
        filters = {"city__iexact": city, "state__iexact": state, "transaction_type": transaction_type}
        events, redirects = events.filter(**filters), redirects.filter(**filters)
    if source is not None:
        events, redirects = events.filter(source_key=source), redirects.filter(source_key=source)
    exposures = events.filter(kind="exposure")
    keys = set(exposures.values_list("source_key", flat=True)) | set(redirects.values_list("source_key", flat=True))
    if source is not None:
        keys.add(source)
    rows = []
    for key in sorted(key for key in keys if key is not None):
        seen, exits = exposures.filter(source_key=key), redirects.filter(source_key=key)
        total = seen.count()
        clicked = seen.filter(redirects__isnull=False).distinct().count()
        historical = (seen.order_by("-created_at").values("source_slug", "source_name").first()
                      or exits.order_by("-created_at").values("source_slug", "source_name").first()
                      or retained_events.filter(source_key=key).order_by("-created_at").values("source_slug", "source_name").first()
                      or retained_redirects.filter(source_key=key).order_by("-created_at").values("source_slug", "source_name").first())
        if not historical:
            item = Source.objects.get(pk=key)
            historical = {"source_slug": item.slug, "source_name": item.name}
        rows.append({"source_id": key, **historical, "exposures": total,
                     "exposures_with_redirect": clicked, "raw_redirects": exits.count(),
                     "attributed_redirects": exits.filter(was_attributed=True).count(),
                     "ctr_percent": round(clicked * 100 / total, 6) if total else None})
    return {
        "start": first.astimezone(zone).isoformat(), "end": last.astimezone(zone).isoformat(),
        "timezone": timezone_name, "extracted_at": now.isoformat(), "observed_until": min(now, last).isoformat(),
        "instrumentation_started_at": window.started_at.isoformat(), "available_from": available.isoformat(),
        "attribution_window_open": last > now - ATTRIBUTION_WINDOW,
        "current_traffic_exclusion": "all" if settings.ANALYTICS_EXCLUDE_ALL else "staff_and_known_automation",
        "searches": events.filter(kind="search").count() if source is None else None,
        "views": events.filter(kind="view").count() if source is None else None,
        "unattributed_searches": unknown_searches, "unattributed_views": unknown_views,
        "source_filter": source, "market": {"city": city, "state": state, "transaction_type": transaction_type},
        "sources": rows,
    }


@transaction.atomic
def purge_events():
    cutoff = timezone.now() - RETENTION
    window, _ = MeasurementWindow.objects.get_or_create(pk=1)
    window = MeasurementWindow.objects.select_for_update().get(pk=window.pk)
    redirects, _ = RedirectEvent.objects.filter(created_at__lte=cutoff).delete()
    events, _ = JourneyEvent.objects.filter(created_at__lte=cutoff).delete()
    window.purged_before = max(cutoff, window.purged_before or cutoff)
    window.save(update_fields=["purged_before"])
    return {"events_deleted": events, "redirects_deleted": redirects, "cutoff": cutoff.isoformat()}
