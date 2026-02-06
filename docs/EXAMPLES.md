# DataExtractor Examples

## Basic HTML Extraction
```python
from src.core.extractor import DataExtractor

extractor = DataExtractor()
html_content = extractor.extract("https://example.com", type="html")
print(html_content)
```

## API Data Fetching
```python
from src.core.extractor import DataExtractor

extractor = DataExtractor()
api_data = extractor.extract(
    "https://api.example.com/data",
    type="api",
    headers={"Authorization": "Bearer token"}
)
print(api_data)
```

## Batch Extraction with Pattern Learning (Simulated)
```python
from src.core.extractor import DataExtractor

extractor = DataExtractor()
urls = [
    "https://shop.com/p/1",
    "https://shop.com/p/2",
    "https://shop.com/p/3"
]
fields = ["name", "price", "stock"]

results = extractor.extract_batch(urls, fields, pattern_learning=True)
for item in results:
    print(item)
```

## PDF Text Extraction
```python
from src.core.extractor import DataExtractor

extractor = DataExtractor()
pdf_text = extractor.extract("path/to/document.pdf", type="pdf")
print(pdf_text)
```

## Database Querying
```python
from src.core.extractor import DataExtractor

extractor = DataExtractor()
db_data = extractor.extract(
    "postgresql://user:pass@localhost/db",
    type="database",
    query="SELECT * FROM users LIMIT 10"
)
print(db_data)
```
