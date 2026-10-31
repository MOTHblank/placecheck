import unicodedata
from dataclasses import dataclass
from decimal import Decimal

from apps.listings.models import Listing
from apps.properties.models import Property

SIMILARITY_THRESHOLD = 0.75


def _normalize_text(value: str | None) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    without_accents = "".join(char for char in normalized if not unicodedata.combining(char))
    return " ".join(without_accents.lower().split())


@dataclass(frozen=True)
class SimilarityResult:
    score: float
    reasons: tuple[str, ...]


def select_candidates(listing: Listing):
    """Reduz o espaço de busca sem exigir que candidatos já tenham Property."""
    return Listing.objects.filter(
        city__iexact=listing.city,
        state__iexact=listing.state,
        property_type=listing.property_type,
    ).exclude(pk=listing.pk)


def _relative_area_similarity(first: Decimal | None, second: Decimal | None) -> float:
    if not first or not second:
        return 0.0
    first_value = Decimal(str(first))
    second_value = Decimal(str(second))
    if first_value <= 0 or second_value <= 0:
        return 0.0
    difference = abs(float(first_value - second_value)) / max(float(first_value), float(second_value))
    return max(0.0, 1.0 - difference / 0.10) if difference <= 0.10 else 0.0


def calculate_similarity(first: Listing, second: Listing) -> SimilarityResult:
    """Calcula similaridade explicável com regras simples para o MVP."""
    score = 0.0
    reasons = []
    if _normalize_text(first.city) == _normalize_text(second.city) and first.state.upper() == second.state.upper():
        score += 0.20
        reasons.append("localização")
    if first.property_type == second.property_type:
        score += 0.20
        reasons.append("tipo")
    if _normalize_text(first.neighborhood) and _normalize_text(first.neighborhood) == _normalize_text(second.neighborhood):
        score += 0.20
        reasons.append("bairro")
    area_score = _relative_area_similarity(first.area, second.area)
    if area_score:
        score += 0.20 * area_score
        reasons.append("área")
    if first.bedrooms is not None and first.bedrooms == second.bedrooms:
        score += 0.10
        reasons.append("quartos")
    if first.bathrooms is not None and first.bathrooms == second.bathrooms:
        score += 0.05
        reasons.append("banheiros")
    if first.parking_spaces is not None and first.parking_spaces == second.parking_spaces:
        score += 0.05
        reasons.append("vagas")
    return SimilarityResult(score=round(score, 4), reasons=tuple(reasons))


def _property_from_listing(listing: Listing) -> Property:
    property_type = listing.property_type
    valid_types = {choice for choice, _ in Property.PropertyType.choices}
    if property_type not in valid_types:
        property_type = Property.PropertyType.OTHER
    return Property.objects.create(
        property_type=property_type,
        city=listing.city,
        state=listing.state,
        neighborhood=listing.neighborhood,
        latitude=listing.latitude,
        longitude=listing.longitude,
        area=listing.area,
        bedrooms=listing.bedrooms,
        bathrooms=listing.bathrooms,
        suites=listing.suites,
        parking_spaces=listing.parking_spaces,
    )


def match_listing_to_property(listing: Listing) -> Property:
    """Associa ao melhor candidato ou cria a entidade física do imóvel."""
    if listing.property_id:
        return listing.property
    best_candidate = None
    best_result = None
    for candidate in select_candidates(listing).filter(property__isnull=False):
        result = calculate_similarity(listing, candidate)
        if best_result is None or result.score > best_result.score:
            best_candidate = candidate
            best_result = result
    property_ = (
        best_candidate.property
        if best_candidate is not None and best_result.score >= SIMILARITY_THRESHOLD
        else _property_from_listing(listing)
    )
    Listing.objects.filter(pk=listing.pk).update(property=property_)
    listing.property = property_
    return property_
