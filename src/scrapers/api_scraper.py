import httpx
from scrapers.base_scraper import BaseScraper


class APIScraper(BaseScraper):
    def scrape(self, source: str, **kwargs) -> dict:
        headers = kwargs.get("headers", {})
        params = kwargs.get("params", {})

        with httpx.Client() as client:
            response = client.get(source, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
