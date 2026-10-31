from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Any

from apps.sources.schemas import RawListing


class ListingProvider(ABC):
    """Contrato de coleta. Providers não conhecem os models do domínio."""

    is_complete_snapshot = False

    @abstractmethod
    def discover(self) -> Iterable[str]:
        raise NotImplementedError

    @abstractmethod
    def fetch(self, reference: str) -> Any:
        raise NotImplementedError

    @abstractmethod
    def parse(self, payload: Any) -> RawListing:
        raise NotImplementedError


class CrawlerProvider(ListingProvider, ABC):
    pass


class ApiProvider(ListingProvider, ABC):
    pass


class XmlFeedProvider(ListingProvider, ABC):
    pass
