class ProviderTemporaryError(Exception):
    """Erro transitório de uma fonte, elegível a retry."""


class SourceRateLimitExceeded(Exception):
    """A fonte atingiu o limite de chamadas no intervalo atual."""
