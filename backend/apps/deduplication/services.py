import math
import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher

from django.conf import settings
from django.db import transaction

from apps.listings.models import Listing
from apps.properties.models import Property
from apps.properties.services import refresh_property
from .models import MatchDecision

SIMILARITY_THRESHOLD = 0.90


def _normalize_text(value):
    normalized = unicodedata.normalize("NFKD", value or "")
    return " ".join("".join(char for char in normalized if not unicodedata.combining(char)).lower().split())


@dataclass(frozen=True)
class SimilarityResult:
    score: float
    reasons: tuple[str, ...]
    automatic: bool = False


def select_candidates(listing):
    return Listing.objects.filter(
        is_active=True, city__iexact=listing.city, state__iexact=listing.state,
        property_type=listing.property_type, property__isnull=False,
    ).exclude(pk=listing.pk).order_by("id")


def _distance(first, second):
    coordinates = (first.latitude, first.longitude, second.latitude, second.longitude)
    if any(value is None for value in coordinates):
        return None
    lat1, lon1, lat2, lon2 = (math.radians(float(value)) for value in coordinates)
    a = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 6371000 * 2 * math.asin(min(1, math.sqrt(a)))


def calculate_similarity(first, second):
    """Require corroborating identity evidence, never demographics alone."""
    for field in ("city", "state", "property_type", "neighborhood", "bedrooms", "bathrooms", "parking_spaces", "suites"):
        a, b = getattr(first, field), getattr(second, field)
        if a not in (None, "") and b not in (None, "") and _normalize_text(str(a)) != _normalize_text(str(b)):
            return SimilarityResult(0, (f"incompatible:{field}",))
    if first.source_id == second.source_id:
        return SimilarityResult(0, ("different-listings-same-source",))
    distance = _distance(first, second)
    if distance is not None and distance > 75:
        return SimilarityResult(0, ("incompatible:coordinates",))
    area_difference = abs(float(first.area) - float(second.area)) / max(float(first.area), float(second.area)) if first.area and second.area else None
    if area_difference is not None and area_difference > 0.05:
        return SimilarityResult(0, ("incompatible:area",))
    unit_pattern = r"\b(?:apto|unidade)\s*(?:n[º°.]?\s*)?(\d+)\b"
    units = [re.search(unit_pattern, _normalize_text(item.title)) for item in (first, second)]
    if all(units) and units[0].group(1) != units[1].group(1):
        return SimilarityResult(0, ("incompatible:unit",))
    title_matches = min(len(first.title), len(second.title)) >= 15 and SequenceMatcher(None, _normalize_text(first.title), _normalize_text(second.title)).ratio() >= 0.90
    close = distance is not None and distance <= getattr(settings, "DEDUP_MAX_AUTO_DISTANCE_METERS", 25)
    area_matches = area_difference is not None and area_difference <= 0.02
    reasons = ["compatible-location-and-characteristics"]
    score = 0.3
    for matches, weight, reason in ((close, 0.3, "nearby-coordinates"), (area_matches, 0.2, "area-within-2-percent"), (title_matches, 0.2, "near-identical-title")):
        if matches:
            score += weight
            reasons.append(reason)
    unit_matches = all(units) and units[0].group(1) == units[1].group(1)
    if unit_matches:
        reasons.append("explicit-unit-identifier")
    else:
        reasons.append("review:missing-explicit-unit")
    automatic = bool(unit_matches and close and area_matches and title_matches and score >= getattr(settings, "DEDUP_AUTO_THRESHOLD", SIMILARITY_THRESHOLD))
    return SimilarityResult(round(score, 4), tuple(reasons), automatic)


def _property_from_listing(listing):
    fields = ("property_type", "city", "state", "neighborhood", "latitude", "longitude", "area", "bedrooms", "bathrooms", "suites", "parking_spaces")
    values = {field: getattr(listing, field) for field in fields}
    if values["property_type"] not in Property.PropertyType.values:
        values["property_type"] = Property.PropertyType.OTHER
    return Property.objects.create(**values)


@transaction.atomic
def match_listing_to_property(listing):
    Listing.objects.select_for_update(no_key=True).get(pk=listing.pk)
    listing.refresh_from_db()
    previous_id = listing.property_id
    group_ids = set(select_candidates(listing).values_list("property_id", flat=True))
    if previous_id:
        group_ids.add(previous_id)
    # Serialize membership decisions, including departures, before reading members.
    # NO KEY UPDATE permits foreign-key references from other ingestions.
    list(Property.objects.select_for_update(no_key=True).filter(pk__in=group_ids).order_by("pk").values_list("pk", flat=True))
    candidates = list(select_candidates(listing).filter(property_id__in=group_ids))
    ranked = sorted(((candidate, calculate_similarity(listing, candidate)) for candidate in candidates), key=lambda pair: (pair[1].automatic, pair[1].score), reverse=True)
    best, result = ranked[0] if ranked else (None, SimilarityResult(0, ("no-candidate",)))
    # Every active member must agree: a bridge cannot join incompatible units.
    automatic_groups = {}
    for member in Listing.objects.filter(is_active=True, property_id__in=group_ids).exclude(pk=listing.pk):
        automatic_groups.setdefault(member.property_id, []).append(calculate_similarity(listing, member).automatic)
    valid_groups = {key for key, values in automatic_groups.items() if all(values)}
    matches = [(candidate, similarity) for candidate, similarity in ranked if similarity.automatic and candidate.property_id in valid_groups]
    if len({candidate.property_id for candidate, _ in matches}) == 1:
        best, result = matches[0]
        assigned = best.property
        outcome = "automatic"
    else:
        peers = Listing.objects.filter(property_id=previous_id, is_active=True).exclude(pk=listing.pk) if previous_id else Listing.objects.none()
        assigned = listing.property if previous_id and not peers.exists() else _property_from_listing(listing)
        outcome = "possible" if result.score >= 0.5 else "separate"
    Listing.objects.filter(pk=listing.pk).update(property=assigned)
    listing.property = assigned
    MatchDecision.objects.create(
        listing=listing, candidate=best, previous_property_id=previous_id,
        assigned_property=assigned, outcome=outcome, score=result.score, reasons=list(result.reasons),
    )
    for property_id in sorted({value for value in (previous_id, assigned.pk) if value}):
        refresh_property(property_id)
    return assigned
