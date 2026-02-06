import pytest
from core.extractor import DataExtractor

def test_extractor_initialization():
    """Verifica que el extractor se inicialice correctamente."""
    extractor = DataExtractor()
    assert extractor is not None
    assert extractor.factory is not None

def test_scraper_factory_invalid_type():
    """Verifica que la factory lance un error con un tipo no soportado."""
    extractor = DataExtractor()
    with pytest.raises(ValueError, match="Unsupported scraper type"):
        extractor.extract("https://example.com", type="invalid_source")

def test_extract_batch_basic():
    """Verifica que el método extract_batch funcione (aunque sea mockeado)."""
    extractor = DataExtractor()
    urls = ["https://example.com"]
    fields = ["title"]
    results = extractor.extract_batch(urls, fields)
    assert isinstance(results, list)
    assert len(results) == 1
