from django.core.management.base import CommandError
from django.db import connection, transaction
from django.db.models import Count, F, Q

from apps.ingestion.models import SyncRun
from apps.listings.models import Listing, ListingPriceHistory
from apps.sources.models import Source
from .reporting import report_market, report_zone


def stock_counts(active, retained):
    counts = active.aggregate(total=Count("pk"), properties=Count("property_id", distinct=True),
                              unassigned=Count("pk", filter=Q(property_id__isnull=True)))
    multiple = active.exclude(property_id=None).order_by().values("property_id").annotate(
        offers=Count("pk")).filter(offers__gte=2).count()
    histories = ListingPriceHistory.objects.filter(listing__in=retained,
        listing__source__can_retain_price_history=True).count()
    return {"active_listings": counts["total"], "represented_properties": counts["properties"],
            "properties_with_multiple_offers": multiple, "retained_price_histories": histories,
            "unassigned_active_listings": counts["unassigned"]}


def grouping_reduction(stock):
    if stock["unassigned_active_listings"]:
        return None, "unassigned_listings"
    total = stock["active_listings"]
    if not total:
        return None, "empty_stock"
    return round((total - stock["represented_properties"]) * 100 / total, 6), None


def run_summary(run, zone):
    if run is None:
        return None
    return {"id": run.pk, "status": run.status, "is_complete": run.is_complete,
            "expected_count": run.expected_count, "processed_count": run.processed_count,
            "deactivated_count": run.deactivated_count, "failure_type": run.failure or None,
            "started_at": run.started_at.astimezone(zone).isoformat(),
            "finished_at": run.finished_at.astimezone(zone).isoformat() if run.finished_at else None}


def inventory_report(*, source=None, city=None, state=None, transaction_type=None, timezone_name="America/Bahia"):
    selected_market = report_market(city, state, transaction_type)
    zone = report_zone(timezone_name)
    if connection.in_atomic_block or not connection.get_autocommit():
        raise CommandError("Execute o relatório fora de outra transação.")
    # A single PostgreSQL snapshot keeps totals, membership and sync status coherent
    # without taking Source/Property locks or blocking ingestion.
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            cursor.execute("SELECT transaction_timestamp()")
            snapshot_at = cursor.fetchone()[0]
        if source is not None and (source < 1 or not Source.objects.filter(pk=source).exists()):
            raise CommandError("Fonte desconhecida.")
        sources = Source.objects.filter(is_demo=False).order_by("pk")
        if source is not None:
            sources = sources.filter(pk=source)
        scoped_listings = Listing.objects.all()
        if selected_market:
            scoped_listings = scoped_listings.filter(city__iexact=city, state__iexact=state,
                                                     transaction_type=transaction_type)
            if source is None:
                # Operational rows can include a now-empty market represented by retained inactive listings.
                sources = sources.filter(pk__in=scoped_listings.values("source_id"))
        source_rows = list(sources)
        published_ids = [item.pk for item in source_rows if item.is_published]
        retained = scoped_listings.filter(source_id__in=published_ids)
        active = retained.filter(is_active=True)
        published_count = active.values("source_id").distinct().count() if selected_market else len(published_ids)
        stock = {"publishable_sources": published_count, **stock_counts(active, retained)}
        reduction, reason = grouping_reduction(stock)
        rows = []
        for item in source_rows:
            source_stock = stock_counts(active.filter(source_id=item.pk), retained.filter(source_id=item.pk))
            source_reduction, source_reason = grouping_reduction(source_stock)
            runs = SyncRun.objects.filter(source_id=item.pk)
            complete = runs.filter(status=SyncRun.Status.SUCCEEDED, is_complete=True,
                                   finished_at__isnull=False).order_by("-finished_at", "-pk").first()
            failure = runs.filter(status=SyncRun.Status.FAILED).order_by(F("finished_at").desc(nulls_last=True), "-pk").first()
            rows.append({"source_id": item.pk, "source_slug": item.slug, "source_name": item.name,
                         "is_published": item.is_published, "collection_paused": not item.is_active,
                         "stock": source_stock, "grouping_reduction_percent": source_reduction,
                         "grouping_reduction_unavailable_reason": source_reason,
                         "synchronization_scope": "whole_source",
                         "latest_run": run_summary(runs.order_by("-pk").first(), zone),
                         "latest_complete_success": run_summary(complete, zone),
                         "latest_failure": run_summary(failure, zone)})
        return {"snapshot_kind": "current", "snapshot_at": snapshot_at.astimezone(zone).isoformat(),
                "timezone": timezone_name, "source_filter": source, "market": selected_market,
                "stock": stock, "grouping_metric": "inventory_reduction",
                "grouping_reduction_percent": reduction, "grouping_reduction_unavailable_reason": reason,
                "sources": rows}
