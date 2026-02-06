from abc import ABC, abstractmethod
from typing import Any


class BaseScraper(ABC):
    """
    Abstract base class for all scrapers.
    """

    @abstractmethod
    def scrape(self, source: str, **kwargs) -> Any:
        pass
