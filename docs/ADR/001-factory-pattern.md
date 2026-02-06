# ADR 001: Use of Factory Pattern for Scrapers

## Status
Accepted

## Context
DataExtractor needs to support multiple data sources (HTML, API, PDF, etc.). Each source requires different libraries and logic.

## Decision
We will use the Factory Pattern to manage scraper instantiation. A central `ScraperFactory` will be responsible for returning the correct scraper based on a string identifier.

## Consequences
- **Pros**: Easy to add new scrapers, clear separation of concerns, centralized configuration.
- **Cons**: Slightly more boilerplate code initially.
