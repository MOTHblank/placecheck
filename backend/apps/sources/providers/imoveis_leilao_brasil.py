"""Limited API pilot: partial discovery and explicit individual availability checks."""

from dataclasses import fields
from datetime import date
from decimal import Decimal, InvalidOperation
import json
import re
import unicodedata
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
from uuid import uuid4

from django.core.cache import cache

from apps.ingestion.exceptions import ProviderTemporaryError
from apps.sources.schemas import RawListing
from .base import ApiProvider

SOURCE_SLUG = "imoveis-leilao-brasil-pilot"
API_URL = "https://www.imoveisleilaobrasil.com.br/api/imoveis"
USER_AGENT = "Placecheck/0.1 (+https://github.com/MOTHblank/placecheck)"
STATES = set("AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO".split())
SALE_METHODS = {
    "venda-direta-online": "asking", "venda-online": "reference",
    "leilao-sfi": "minimum", "licitacao-aberta": "minimum",
}
PROPERTY_TYPES = {
    "apartamento": "apartment", "casa": "house", "sobrado": "house",
    "terreno": "land", "predio": "commercial", "sala-comercial": "commercial",
    "loja": "commercial", "galpao": "commercial", "comercial": "commercial",
    "rural": "other", "outros": "other",
}
PUBLIC_FIELDS = {
    "id", "tipoSlug", "cidade", "cidadeSlug", "uf", "bairro", "preco",
    "areaPrivativa", "areaTerreno", "quartos", "vagas", "modalidade", "modalidadeSlug", "linkOficial",
}


def _slug(value):
    text = unicodedata.normalize("NFKD", value)
    return re.sub(r"[^a-z0-9]+", "-", "".join(c for c in text if not unicodedata.combining(c)).lower()).strip("-")


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class ImoveisLeilaoBrasilClient:
    def search(self, *, uf, city, limit):
        query = urlencode({"uf": uf.lower(), "cidade": city, "limite": limit,
                           "pagina": 1, "ordem": "preco-menor"})
        return self._get_json(f"{API_URL}?{query}")

    def detail(self, external_id):
        if not isinstance(external_id, str) or not re.fullmatch(r"\d{5,20}", external_id):
            raise ValueError("ID CAIXA inválido.")
        return self._get_json(f"https://www.imoveisleilaobrasil.com.br/api/imovel/{external_id}", allow_missing=True)

    def _get_json(self, url, *, allow_missing=False):
        request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
        try:
            with build_opener(_NoRedirect()).open(request, timeout=8) as response:
                body = response.read(1_048_577)
        except HTTPError as error:
            try:
                if allow_missing and error.code == 404:
                    content_type = (error.headers or {}).get("Content-Type", "").split(";")[0].strip().lower()
                    payload = self._decode(error.read(1_048_577))
                    # Observed API marker; an HTML/proxy/error-page 404 is not evidence.
                    if content_type == "application/json" and payload == {"erro": "nao encontrado"}:
                        return None
                    raise ValueError("Ausência ILB não confirmada pelo contrato JSON.")
            except (TimeoutError, OSError):
                raise ProviderTemporaryError("Falha ao ler a resposta de disponibilidade ILB.") from None
            finally:
                error.close()
            if error.code == 429 or 500 <= error.code < 600:
                raise ProviderTemporaryError("API ILB temporariamente indisponível.") from None
            raise ValueError("API ILB recusou a consulta; nenhum inventário confirmado.") from None
        except (URLError, TimeoutError, OSError):
            raise ProviderTemporaryError("Falha de transporte na API ILB.") from None
        return self._decode(body)

    def _decode(self, body):
        if len(body) > 1_048_576:
            raise ValueError("Resposta ILB excedeu o limite de 1 MiB.")
        try:
            payload = json.loads(body, parse_float=Decimal)
        except (ValueError, UnicodeError):
            raise ValueError("JSON ILB inválido.") from None
        if not isinstance(payload, dict):
            raise ValueError("Objeto JSON ILB inválido.")
        return payload


def _number(item, name, *, integer=False):
    value = item.get(name)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise ValueError(f"Campo numérico ILB inválido: {name}.")
    try:
        number = Decimal(str(value))
    except InvalidOperation:
        raise ValueError(f"Campo numérico ILB inválido: {name}.") from None
    maximum = Decimal("32767") if integer else Decimal("999999999999.99")
    if not number.is_finite() or number < 0 or number > maximum or (integer and number != number.to_integral_value()):
        raise ValueError(f"Campo numérico ILB fora da faixa: {name}.")
    return int(number) if integer else number


class ImoveisLeilaoBrasilProvider(ApiProvider):
    def __init__(self, *, uf, city, limit=10, client=None):
        if not isinstance(uf, str) or uf.upper() not in STATES:
            raise ValueError("Configure uma UF válida para o piloto ILB.")
        if not isinstance(city, str) or len(city) > 120 or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", city):
            raise ValueError("Configure o slug de uma cidade para o piloto ILB.")
        if type(limit) is not int or not 1 <= limit <= 20:
            raise ValueError("O piloto ILB aceita de 1 a 20 anúncios por captura parcial.")
        self.uf, self.city, self.limit = uf.upper(), city, limit
        self.client = client or ImoveisLeilaoBrasilClient()

    def check_availability(self, external_id):
        item = self.client.detail(external_id)
        if item is None:
            return False
        raw = self.parse(item)
        if raw.source_external_id != external_id:
            raise ValueError("Detalhe ILB pertence a outro ID.")
        return True

    def _cached_references(self, scope):
        snapshot = cache.get(f"ilb:catalog:{scope}")
        if snapshot:
            records = cache.get(f"ilb:snapshot:{snapshot}")
            if records and records["scope"] == scope:
                return [f"{snapshot}:{key}" for key in records["items"]]
        return None

    def discover(self):
        scope = f"{self.uf}:{self.city}:{self.limit}"
        catalog_key = f"ilb:catalog:{scope}"
        references = self._cached_references(scope)
        if references is not None:
            return references
        lock_key = f"ilb:download:{scope}"
        # Outlive the task's 45 s hard limit; another task cannot steal a live capture.
        if not cache.add(lock_key, True, timeout=60):
            raise ProviderTemporaryError("Captura ILB já está em andamento.")
        try:
            references = self._cached_references(scope)
            if references is not None:
                return references
            page = self.client.search(uf=self.uf, city=self.city, limit=self.limit)
            if not isinstance(page, dict) or type(page.get("total")) is not int or page["total"] < 0:
                raise ValueError("Envelope ILB inválido.")
            if page.get("pagina") != 1 or page.get("limite") != self.limit:
                raise ValueError("Paginação ILB incompatível com o recorte.")
            try:
                date.fromisoformat(page["listaGeradaEm"])
            except (KeyError, TypeError, ValueError):
                raise ValueError("Data do inventário ILB inválida.") from None
            items = page.get("resultados")
            if not isinstance(items, list) or len(items) > self.limit or len(items) > page["total"]:
                raise ValueError("Lista ILB inválida.")
            records = {}
            for item in items:
                if not isinstance(item, dict):
                    raise ValueError("Anúncio ILB inválido.")
                item = {key: value for key, value in item.items() if key in PUBLIC_FIELDS}
                item["source_inventory_date"] = page["listaGeradaEm"]
                raw = self.parse(item)
                if raw.source_external_id in records:
                    raise ValueError("ID repetido na captura ILB.")
                records[raw.source_external_id] = item
            snapshot = uuid4().hex
            cache.set(f"ilb:snapshot:{snapshot}", {"scope": scope, "items": records}, timeout=90_000)
            cache.set(catalog_key, snapshot, timeout=86_400)
            return [f"{snapshot}:{key}" for key in records]
        finally:
            cache.delete(lock_key)

    def fetch(self, reference):
        if not isinstance(reference, str) or not re.fullmatch(r"[a-f0-9]{32}:\d{5,20}", reference):
            raise ValueError("Referência ILB inválida.")
        snapshot, external_id = reference.split(":")
        records = cache.get(f"ilb:snapshot:{snapshot}")
        scope = f"{self.uf}:{self.city}:{self.limit}"
        if not records or records["scope"] != scope or external_id not in records["items"]:
            raise ValueError("Captura ILB indisponível; não reconciliar ausências.")
        return records["items"][external_id]

    def parse(self, item):
        if not isinstance(item, dict):
            raise ValueError("Anúncio ILB inválido.")
        external_id = item.get("id")
        if not isinstance(external_id, str) or not re.fullmatch(r"\d{5,20}", external_id):
            raise ValueError("ID CAIXA inválido.")
        city, state = item.get("cidade"), item.get("uf")
        if not isinstance(city, str) or not city.strip() or len(city) > 120 or _slug(city) != self.city or state != self.uf:
            raise ValueError("Anúncio ILB fora do recorte configurado.")
        neighborhood = item.get("bairro") or ""
        if not isinstance(neighborhood, str) or len(neighborhood) > 120:
            raise ValueError("Bairro ILB inválido.")
        method_text = item.get("modalidade")
        if not isinstance(method_text, str):
            raise ValueError("Modalidade ILB ausente.")
        method = _slug(method_text)
        if method not in SALE_METHODS or item.get("modalidadeSlug", method) not in (None, method):
            raise ValueError("Modalidade ILB não suportada.")
        property_type = PROPERTY_TYPES.get(item.get("tipoSlug"))
        if property_type is None:
            raise ValueError("Tipo de imóvel ILB não suportado.")
        url = item.get("linkOficial")
        if not isinstance(url, str) or len(url) > 200:
            raise ValueError("Link oficial CAIXA ausente ou inválido.")
        try:
            parsed = urlsplit(url)
            valid = (parsed.scheme == "https" and parsed.hostname == "venda-imoveis.caixa.gov.br"
                     and parsed.port in (None, 443) and not parsed.username and not parsed.password
                     and not parsed.fragment and parsed.path == "/sistema/detalhe-imovel.asp"
                     and parse_qs(parsed.query) == {"hdnimovel": [external_id]})
        except ValueError:
            valid = False
        if not valid:
            raise ValueError("Destino diferente da ficha oficial CAIXA.")
        area_field = "areaTerreno" if property_type == "land" else "areaPrivativa"
        area = _number(item, area_field)
        if area is not None and area > Decimal("9999999999.99"):
            raise ValueError("Área ILB fora da faixa.")
        values = {field.name: None for field in fields(RawListing)}
        values.update(source_external_id=external_id, title=f"{item['tipoSlug']} — {method_text} — CAIXA {external_id}",
                      description="", transaction_type="sale", property_type=property_type,
                      price=_number(item, "preco"), area=area, bedrooms=_number(item, "quartos", integer=True),
                      parking_spaces=_number(item, "vagas", integer=True), city=city, state=state,
                      neighborhood=neighborhood, url=url, sale_method=method, price_kind=SALE_METHODS[method])
        values["source_inventory_date"] = item.get("source_inventory_date")
        return RawListing(**values)
