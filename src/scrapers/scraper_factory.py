from typing import Dict, Type
from scrapers.html_scraper import HTMLScraper
from scrapers.api_scraper import APIScraper
from scrapers.javascript_scraper import JSScraper
from scrapers.pdf_scraper import PDFScraper
from scrapers.database_scraper import DatabaseScraper


class ScraperFactory:
    """
    Factory pattern to manage different types of scrapers.
    """

    _scrapers = {
        "html": HTMLScraper,
        "api": APIScraper,
        "spa": JSScraper,
        "pdf": PDFScraper,
        "database": DatabaseScraper,
    }

    def get_scraper(self, scraper_type: str):
        scraper_class = self._scrapers.get(scraper_type.lower())
        if not scraper_class:
            raise ValueError(f"Unsupported scraper type: {scraper_type}")
        return scraper_class()
