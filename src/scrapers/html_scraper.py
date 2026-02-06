import httpx
from bs4 import BeautifulSoup
from src.scrapers.base_scraper import BaseScraper

class HTMLScraper(BaseScraper):
    def scrape(self, source: str, **kwargs) -> str:
        response = httpx.get(source)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        # Basic implementation: return the whole text or soup object
        return str(soup)
