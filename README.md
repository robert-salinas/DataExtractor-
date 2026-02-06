# 🕷️ DataExtractor (DX) v0.1.0

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://github.com/robert-salinas/DataExtractor-/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/robert-salinas/DataExtractor-/actions)
[![Build Status](https://github.com/robert-salinas/DataExtractor-/actions/workflows/lint.yml/badge.svg?branch=main)](https://github.com/robert-salinas/DataExtractor-/actions)

**"Herramienta flexible y potente para extraer datos de cualquier fuente web. Desde sitios simples HTML hasta aplicaciones JavaScript complejas, todo desde una única plataforma inteligente."**

> **Slogan:** Extract. Transform. Analyze. Repeat.

---

## ✨ Lo que DataExtractor HACE DIFERENTE

DataExtractor es un **motor de extracción de datos de próxima generación** diseñado para automatizar la recolección de información web mediante inteligencia de patrones, reduciendo la curva de aprendizaje y el mantenimiento técnico.

### 1. 🔗 Multi-Source Intelligence
DataExtractor entiende múltiples fuentes de UNA VEZ sin configuraciones manuales complejas. Desde HTML estándar hasta JavaScript dinámico, APIs REST y bases de datos, todo funciona bajo la misma interfaz.

```python
from src.core.extractor import DataExtractor

extractor = DataExtractor()

# HTML estándar
data = extractor.extract("https://example.com", type="html")

# JavaScript dinámico (SPA - Single Page Applications)
data = extractor.extract("https://spa-app.com", type="spa")

# API REST
data = extractor.extract("https://api.example.com/data", type="api")

# PDF extraído
data = extractor.extract("file.pdf", type="pdf")

# Bases de datos
data = extractor.extract(
    "postgresql://user:pass@localhost/db", 
    type="database", 
    query="SELECT * FROM products"
)
```

### 2. 🎯 No-Code/Low-Code Interface
Diseñado para que **cualquier persona** pueda extraer datos sin escribir código:
1. Abre **DataExtractor Web UI**.
2. Pega la URL o configura la fuente.
3. Click en **"Smart Extraction"**.
4. ¡Listo! Exporta a CSV, JSON, Excel o cualquier formato.

### 3. 🧠 Intelligent Field Detection
Olvida los selectores CSS manuales complejos:
- ❌ **Antes:** "Define el selector CSS: `div.product > span.price`"
- ✅ **Ahora:** "¿Qué quieres extraer?" → *"Quiero precios y títulos"* → **DataExtractor lo encuentra automáticamente**

El sistema utiliza **análisis semántico del DOM** para identificar patrones de datos sin intervención manual.

### 4. 📚 Pattern Learning
DataExtractor **aprende** de la estructura de las páginas. A medida que extraes de más páginas similares, el sistema se vuelve más robusto y requiere menos mantenimiento. La primera página se analiza automáticamente; las subsiguientes aplican el patrón aprendido.

```python
# Extrae de 1 página, aprende estructura
data = extractor.extract_batch(
    urls=["amazon.com/s?k=laptop"],
    fields=["title", "price", "rating"],
    pattern_learning=True
)
```

### 5. 📤 Multi-Format Output
Extrae **una sola vez**, exporta a **múltiples formatos**:
- CSV / JSON / Excel / Parquet / XML
- SQL INSERT statements (listo para insertar en BD)
- Webhooks / Email / Cloud Storage

---

## 🛠️ Stack Tecnológico

- **Backend:** Python 3.11+, FastAPI, Celery, Redis, SQLAlchemy.
- **Scraping:** BeautifulSoup 4, Playwright, Selenium, httpx.
- **Frontend:** Vue 3, Tailwind CSS, Shadcn/ui.
- **Infra:** Docker, GitHub Actions.

---

## � Instalación Rápida (< 5 minutos)

```bash
# 1. Clonar el repositorio
git clone https://github.com/robert-salinas/DataExtractor-.git
cd DataExtractor-

# 2. Instalar dependencias
pip install -e .
```

---

## 📖 Documentación y Comunidad

Para más detalles sobre cómo funciona DataExtractor, consulta los siguientes recursos:

- 🏛️ [Arquitectura](docs/ARCHITECTURE.md)
- 📝 [Decisiones de Diseño (ADRs)](docs/ADR/)
- 🕹️ [Ejemplos de Uso](docs/EXAMPLES.md)
- 🤝 [Guía de Contribución](CONTRIBUTING.md)
- 📜 [Código de Conducta](CODE_OF_CONDUCT.md)

---

## 👨‍💻 Autor

Desarrollado con ❤️ por **[Robert Salinas](https://github.com/robert-salinas)**.

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Consulta el archivo [LICENSE](LICENSE) para más detalles.
