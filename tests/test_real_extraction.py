import pytest
from unittest.mock import MagicMock, patch
from src.scrapers.html_scraper import HTMLScraper

@pytest.fixture
def mock_html_response():
    html_content = """
    <html>
        <body>
            <div id="product-1" class="product">
                <h1 class="title">Smartphone X</h1>
                <span class="price">$999</span>
                <p class="description">Best phone ever.</p>
            </div>
        </body>
    </html>
    """
    mock_response = MagicMock()
    mock_response.text = html_content
    mock_response.raise_for_status.return_value = None
    return mock_response

def test_scrape_with_selectors(mock_html_response):
    scraper = HTMLScraper()
    
    with patch("httpx.get", return_value=mock_html_response):
        # Define fields and selectors
        fields = ["name", "cost"]
        selectors = {
            "name": "h1.title",
            "cost": ".price"
        }
        
        results = scraper.scrape("http://fake-url.com", fields=fields, selectors=selectors)
        
        assert len(results) == 1
        item = results[0]
        assert item["name"] == "Smartphone X"
        assert item["cost"] == "$999"

def test_scrape_fallback_heuristic(mock_html_response):
    scraper = HTMLScraper()
    
    with patch("httpx.get", return_value=mock_html_response):
        # Define fields without selectors (relying on heuristic)
        # "title" matches class="title"
        # "price" matches class="price"
        fields = ["title", "price"]
        
        results = scraper.scrape("http://fake-url.com", fields=fields)
        
        assert len(results) == 1
        item = results[0]
        assert item["title"] == "Smartphone X"
        assert item["price"] == "$999"

def test_scrape_mixed_mode(mock_html_response):
    scraper = HTMLScraper()
    
    with patch("httpx.get", return_value=mock_html_response):
        fields = ["name", "price"]
        selectors = {
            "name": "h1.title"
            # price has no selector, should fallback
        }
        
        results = scraper.scrape("http://fake-url.com", fields=fields, selectors=selectors)
        
        assert len(results) == 1
        item = results[0]
        assert item["name"] == "Smartphone X"
        assert item["price"] == "$999"
