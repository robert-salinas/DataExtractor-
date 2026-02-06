# Arquitectura del Sistema 🏛️

## Descripción General

**DataExtractor (DX)** está diseñado bajo una arquitectura modular y orientada a servicios para permitir la máxima flexibilidad en la extracción de datos de diversas fuentes.

## Componentes Principales

1.  **Core (Orquestación):** Maneja el flujo principal de datos y coordina los scrapers y extractores.
2.  **Scrapers (Motores):** Implementaciones específicas para cada protocolo (HTTP, API, PDF, SQL).
3.  **Extractors (Inteligencia):** Capa de análisis semántico para detección de campos y aprendizaje de patrones.
4.  **API/CLI:** Interfaces de interacción para usuarios y sistemas externos.

## Decisiones de Diseño

- **Patrón Factory:** Utilizado en los scrapers para instanciar el motor adecuado dinámicamente.
- **Asyncio:** Uso extensivo de procesamiento asíncrono para mejorar el rendimiento en extracciones masivas.
- **Pydantic:** Validación estricta de esquemas de datos en la API.

---
Desarrollado por Robert Salinas.
