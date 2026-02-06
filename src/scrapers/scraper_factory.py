from typing import Dict, Type
from src.scrapers.html_scraper import HTMLScraper
from src.scrapers.api_scraper import APIScraper
from src.scrapers.javascript_scraper import JSScraper
from src.scrapers.pdf_scraper import PDFScraper
from src.scrapers.database_scraper import DatabaseScraper

class ScraperFactory:
    """
    Factory pattern to manage different types of scrapers.
    """
    
    _scrapers = {
        "html": HTMLScraper,
        "api": APIScraper,
        "spa": JSScraper,
        "pdf": PDFScraper,
        "database": DatabaseScraper
    }

    def get_scraper(self, scraper_type: str):
        scraper_class = self._scrapers.get(scraper_type.lower())
        if not scraper_class:
            raise ValueError(f"Unsupported scraper type: {scraper_type}")
        return scraper_class()
