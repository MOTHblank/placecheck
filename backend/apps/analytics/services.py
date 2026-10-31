from datetime import timedelta
import json
import re
from uuid import UUID

from django.conf import settings
from django.core import signing
from django.db import transaction
from django.http import Http404
from django.utils import timezone
from django.utils.crypto import salted_hmac
from rest_framework.exceptions import APIException, ValidationError

from apps.listings.models import Listing
from apps.sources.models import Source
from .models import JourneyEvent, MeasurementWindow, RedirectEvent

RETENTION = timedelta(days=90)
ATTRIBUTION_WINDOW = timedelta(minutes=30)
SALT = "placecheck.analytics.v1"
AUTOMATION = re.compile(r"bot\b|spider|crawler|headlesschrome|playwright|pytest|curl/|python-urllib", re.I)


class IdentityConflict(APIException):
    status_code = 409
    default_detail = "Identidade de evento já usada com outro conteúdo."


def measurable(request):
    origin = request.headers.get("Origin")
    if origin and origin != f"{request.scheme}://{request.get_host()}":
        return False
    return not (settings.ANALYTICS_EXCLUDE_ALL or getattr(request.user, "is_staff", False)
                or AUTOMATION.search(request.META.get("HTTP_USER_AGENT", "")))


def digest(value):
    content = json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))
    return salted_hmac("analytics-content", content, algorithm="sha256").hexdigest()


def signed(value):
    return signing.dumps(value, salt=SALT, compress=True)


def unsigned(value, purpose, *, max_age=RETENTION.total_seconds()):
    try:
        data = signing.loads(value, salt=SALT, max_age=max_age)
        if not isinstance(data, dict) or data.get("purpose") != purpose:
            raise signing.BadSignature()
        return data
    except (signing.BadSignature, TypeError, ValueError):
        raise ValidationError("Comprovante de medição inválido ou expirado.") from None


def market(city="", state="", transaction_type=""):
    if not city or not state or transaction_type not in ("sale", "rent"):
        return {"city": "", "state": "", "transaction_type": ""}
    return {"city": city, "state": state.upper(), "transaction_type": transaction_type}


def snapshot(listing):
    return {"source_key": listing.source_id, "source_slug": listing.source.slug,
            "source_name": listing.source.name, **market(listing.city, listing.state, listing.transaction_type)}


def receipt(request, kind, params, *, offers, property_=None):
    if not measurable(request):
        return None
    eligible = offers.filter(source__is_demo=False, source__can_retain_analytics=True)
    values = {"purpose": f"{kind}_receipt", "query_digest": digest(params)}
    if kind == "search":
        if offers.exists() and not eligible.exists():
            return None
        city, state = params.get("city", ""), params.get("state", "")
        canonical = Listing.objects.filter(city__iexact=city, state__iexact=state,
            source__is_published=True, source__is_demo=False).values_list("city", flat=True).first()
        values["market"] = market(canonical or "", state, params.get("transaction_type", ""))
    else:
        ids = list(eligible.values_list("pk", flat=True))
        if not ids:
            return None
        values.update(property=property_.pk, offers=ids,
                      market=market(property_.city, property_.state, params.get("transaction_type", "")))
    return signed(values)


def event_result(event, data):
    result = {"accepted": True, "event_id": str(event.pk)}
    if event.kind == "view":
        result["context_token"] = signed({"purpose": "context", "view": str(event.pk),
                                          "property": event.property_key, "offers": data["offers"]})
    elif event.kind == "exposure":
        result["redirect_token"] = signed({"purpose": "exit", "exposure": str(event.pk),
                                           "context": str(event.context_id), "listing": event.listing_key,
                                           "source": event.source_key})
    return result


@transaction.atomic
def accept_event(request, payload):
    if not measurable(request):
        return {"accepted": False}, False
    MeasurementWindow.objects.get_or_create(pk=1, defaults={"started_at": timezone.now()})
    kind = payload["kind"]
    values = {"kind": kind, "context_id": payload["event_id"]}
    if kind in ("search", "view"):
        data = unsigned(payload.get("receipt"), f"{kind}_receipt", max_age=1800)
        identity = {"kind": kind, "receipt": data}
        values.update(data["market"])
        if kind == "view":
            values["property_key"] = data["property"]
    else:
        data = unsigned(payload.get("context"), "context")
        listing_id = payload.get("listing_id")
        if listing_id not in data["offers"]:
            raise ValidationError("Oferta não pertence ao contexto de abertura.")
        identity = {"kind": kind, "context": data, "listing": listing_id}
        values.update(context_id=UUID(data["view"]), property_key=data["property"], listing_key=listing_id)
    fingerprint = digest({"event": str(payload["event_id"]), "payload": identity})
    existing = JourneyEvent.objects.filter(pk=payload["event_id"]).first()
    if existing:
        if existing.payload_digest != fingerprint:
            raise IdentityConflict()
        return event_result(existing, data), False
    if kind == "view":
        if not Listing.objects.filter(pk__in=data["offers"], property_id=data["property"], is_active=True,
            source__is_published=True, source__is_demo=False, source__can_retain_analytics=True).exists():
            return {"accepted": False}, False
    if kind == "exposure":
        source_id = Listing.objects.filter(pk=listing_id).values_list("source_id", flat=True).first()
        source = Source.objects.select_for_update().filter(pk=source_id).first()
        if not source or not source.is_published or source.is_demo or not source.can_retain_analytics:
            return {"accepted": False}, False
        if not JourneyEvent.objects.filter(pk=values["context_id"], kind="view",
                                           created_at__gt=timezone.now() - RETENTION).exists():
            raise ValidationError("Contexto de abertura indisponível.")
        # Read membership, activity and market only after preceding ingestion/reconciliation committed.
        listing = Listing.objects.select_related("source").filter(
            pk=listing_id, source_id=source.pk, property_id=data["property"], is_active=True,
        ).first()
        if not listing:
            return {"accepted": False}, False
        recorded = JourneyEvent.objects.filter(kind="exposure", context_id=values["context_id"], listing_key=listing_id).first()
        if recorded:
            if recorded.pk == payload["event_id"] and recorded.payload_digest == fingerprint:
                return event_result(recorded, data), False
            raise IdentityConflict("Oferta já exposta nesta abertura; reutilize a identidade original.")
        listing.source = source
        values.update(snapshot(listing))
    event, created = JourneyEvent.objects.get_or_create(pk=payload["event_id"], defaults={
        **values, "payload_digest": fingerprint, "created_at": timezone.now(),
    })
    if event.payload_digest != fingerprint:
        raise IdentityConflict()
    return event_result(event, data), created


@transaction.atomic
def record_redirect(request, listing):
    # Serialize permission withdrawal with writes, just as ingestion does.
    try:
        Source.objects.select_for_update().get(pk=listing.source_id)
        listing = Listing.objects.select_related("source", "property").get(
            pk=listing.pk, is_active=True, source__is_published=True)
    except (Source.DoesNotExist, Listing.DoesNotExist):
        raise Http404 from None
    if not measurable(request) or listing.source.is_demo or not listing.source.can_retain_analytics:
        return listing
    MeasurementWindow.objects.get_or_create(pk=1, defaults={"started_at": timezone.now()})
    now = timezone.now()
    exposure = None
    token = request.query_params.get("exposure")
    if token:
        try:
            data = unsigned(token, "exit")
            if data.get("listing") == listing.pk and data.get("source") == listing.source_id:
                exposure = JourneyEvent.objects.filter(
                    pk=data["exposure"], kind="exposure", context_id=data["context"],
                    listing_key=listing.pk, source_key=listing.source_id,
                    created_at__lte=now, created_at__gt=now - ATTRIBUTION_WINDOW,
                ).first()
        except (ValidationError, ValueError, KeyError):
            pass
    RedirectEvent.objects.create(listing=listing, listing_key=listing.pk, property=listing.property,
                                 exposure=exposure, was_attributed=exposure is not None, created_at=now, **snapshot(listing))
    return listing
