from rest_framework.schemas.openapi import AutoSchema

from .filters import SearchParameters


class PropertySchema(AutoSchema):
    def map_field(self, field):
        if field.field_name == "days_on_market":
            return {"type": "integer", "minimum": 0}
        return super().map_field(field)

    def get_filter_parameters(self, path, method):
        return [
            {"name": name, "in": "query", "required": False, "schema": self.map_field(field)}
            for name, field in SearchParameters().fields.items()
        ]

    def get_responses(self, path, method):
        responses = super().get_responses(path, method)
        if "{id}" not in path:
            schema = responses.get("200", {}).get("content", {}).get("application/json", {}).get("schema", {})
            schema.setdefault("properties", {})["analytics_receipt"] = {"type": "string", "nullable": True, "description": "Comprovante assinado de resultados carregados; não registra Busca automaticamente."}
        responses["400"] = {"description": "Parâmetros inválidos ou intervalo invertido."}
        if "{id}" in path:
            responses["404"] = {"description": "Imóvel sem ofertas publicáveis correspondentes."}
        return responses


class RedirectSchema(AutoSchema):
    def get_filter_parameters(self, path, method):
        return [{"name": "exposure", "in": "query", "required": False,
                 "schema": {"type": "string"}, "description": "Token de exposição aceito pela API; ausente/inválido resulta somente em saída bruta."}]

    def get_responses(self, path, method):
        return {
            "302": {"description": "Saída registrada; Location contém a URL original.", "headers": {"Location": {"schema": {"type": "string", "format": "uri"}}}},
            "404": {"description": "Anúncio inexistente, inativo ou retirado."},
        }
