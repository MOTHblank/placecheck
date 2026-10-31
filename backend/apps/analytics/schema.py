from rest_framework.schemas.openapi import AutoSchema


class EventSchema(AutoSchema):
    def get_responses(self, path, method):
        accepted = {"description": "Evento aceito; context_token para view e redirect_token para exposure.",
                    "content": {"application/json": {"schema": {"type": "object", "properties": {
                        "accepted": {"type": "boolean"}, "event_id": {"type": "string", "format": "uuid"},
                        "context_token": {"type": "string"}, "redirect_token": {"type": "string"},
                    }}}}}
        return {"201": accepted, "200": {**accepted, "description": "Retransmissão idempotente."},
                "202": {"description": "Tráfego ou oferta excluídos; accepted=false."},
                "400": {"description": "Identidade, comprovante ou contexto inválidos."},
                "409": {"description": "Identidade reutilizada com conteúdo diferente."}}
