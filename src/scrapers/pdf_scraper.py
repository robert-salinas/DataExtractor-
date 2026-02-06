from PyPDF2 import PdfReader
from scrapers.base_scraper import BaseScraper


class PDFScraper(BaseScraper):
    def scrape(self, source: str, **kwargs) -> str:
        reader = PdfReader(source)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
