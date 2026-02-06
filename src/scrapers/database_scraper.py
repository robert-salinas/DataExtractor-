from sqlalchemy import create_engine, text
from src.scrapers.base_scraper import BaseScraper

class DatabaseScraper(BaseScraper):
    def scrape(self, source: str, **kwargs) -> list:
        query = kwargs.get('query')
        if not query:
            raise ValueError("A SQL query must be provided for database extraction.")
            
        engine = create_engine(source)
        with engine.connect() as connection:
            result = connection.execute(text(query))
            return [dict(row) for row in result.mappings()]
