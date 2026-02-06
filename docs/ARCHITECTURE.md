# DataExtractor Architecture

DataExtractor (DX) is designed with modularity and scalability in mind. It follows several design patterns to ensure flexibility across different data sources.

## Core Components

### 1. DataExtractor (Core)
The main entry point (`src/core/extractor.py`) that coordinates extraction requests. It uses a `ScraperFactory` to delegate tasks.

### 2. Scraper Factory
Located in `src/scrapers/scraper_factory.py`, this component instantiates the appropriate scraper based on the source type (HTML, API, SPA, PDF, Database).

### 3. Base Scraper
An abstract base class (`src/scrapers/base_scraper.py`) that defines the interface for all scrapers, ensuring consistency.

### 4. Specialized Scrapers
- **HTML Scraper**: Uses BeautifulSoup and HTTPX for static content.
- **API Scraper**: Handles JSON/REST responses.
- **JS Scraper**: (SPA) Designed to use Playwright or Selenium for dynamic rendering.
- **PDF Scraper**: Extracts text from PDF files.
- **Database Scraper**: Executes SQL queries against various databases using SQLAlchemy.

## Data Flow
1. User calls `DataExtractor.extract(source, type)`.
2. `DataExtractor` asks `ScraperFactory` for the correct scraper.
3. `ScraperFactory` returns a specialized scraper instance.
4. `DataExtractor` calls `scraper.scrape(source)`.
5. The scraper returns the processed data to the core, which returns it to the user.

## Future Enhancements
- **Intelligent Field Detection**: AI-powered identification of relevant data fields.
- **Pattern Learning**: Automatic learning of extraction patterns for batch processing.
- **Distributed Processing**: Integration with Celery and Redis for high-volume tasks.
