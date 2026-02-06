# ADR-0002: Estrategia de Scrapers Multifuente

## Estado
Aceptado

## Contexto
El sistema debe manejar HTML, APIs, PDFs y DBs de forma transparente para el usuario.

## Decisión
Implementar un patrón **Factory** que encapsule la lógica de cada fuente, exponiendo un método `scrape()` común a través de una clase base abstracta.

## Consecuencias
- Desacoplamiento total entre la lógica de negocio y los protocolos de extracción.
- Facilidad para añadir nuevas fuentes en el futuro.
