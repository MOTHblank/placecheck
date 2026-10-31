import logging
import re


class RedactAttribution(logging.Filter):
    """Access logs must not become a parallel store of individual exposure tokens."""

    def filter(self, record):
        if record.name.startswith("django.server") or record.name.startswith("django.request"):
            record.msg = re.sub(r"(/(?:out/\d+|api/properties(?:/\d+)?)/)\?[^\s\"]+", r"\1?[redacted]", record.getMessage())
            record.args = ()
        return True
