# 🕷️ DataExtractor (DX) v0.1.0

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

# El sistema automáticamente:
# 1. Identifica dónde están título, precio y rating
# 2. Aplica ese conocimiento a otras páginas
# 3. Se adapta a cambios menores en el DOM
```

### 5. 📤 Multi-Format Output
Extrae **una sola vez**, exporta a **múltiples formatos**:
- CSV / JSON / Excel / Parquet / XML
- SQL INSERT statements (listo para insertar en BD)
- Webhooks (notificaciones HTTP)
- Email (envío automático de reportes)
- Cloud Storage (S3, Google Cloud, Azure)

---

## 🛠️ Stack Tecnológico

**Backend:**
- Python 3.11+ (lenguaje principal)
- FastAPI (servidor API de alto rendimiento)
- Celery + Redis (procesamiento async y scheduling)
- SQLAlchemy + Pydantic (ORM y validación de datos)
- PostgreSQL (persistencia principal)

**Scraping & Extracción:**
- BeautifulSoup 4 (parsing semántico de HTML)
- Playwright / Selenium (renderización de JavaScript)
- httpx (cliente HTTP moderno)
- PyPDF2 (extracción de PDFs)

**Análisis de Datos:**
- Pandas (transformación y limpieza)
- Regex patterns (extracción inteligente)

**Frontend:**
- Vue 3 (interfaz reactiva)
- Tailwind CSS (diseño accesible)
- Shadcn/ui (componentes polished)

**DevOps & Testing:**
- Docker + Docker Compose (contenerización)
- GitHub Actions (CI/CD automático)
- Pytest (tests unitarios e integración)

---

## 📁 Estructura del Proyecto

```text
data-extractor/
├── src/
│   ├── core/
│   │   ├── extractor.py        # Clase principal de orquestación
│   │   ├── pipelines.py        # Flujos de extracción
│   │   └── cache.py            # Sistema de caché inteligente
│   │
│   ├── scrapers/
│   │   ├── html_scraper.py     # Extracción de HTML estándar
│   │   ├── api_scraper.py      # Consumo de APIs REST
│   │   ├── javascript_scraper.py # Renderización JavaScript
│   │   ├── pdf_scraper.py      # Extracción de PDFs
│   │   ├── database_scraper.py # Conexión a bases de datos
│   │   └── scraper_factory.py  # Factory pattern
│   │
│   ├── extractors/
│   │   ├── field_detector.py   # Detección automática de campos
│   │   ├── pattern_learner.py  # Aprendizaje de patrones
│   │   ├── data_classifier.py  # Clasificación de datos
│   │   └── transformer.py      # Limpieza y normalización
│   │
│   ├── api/
│   │   ├── main.py             # Aplicación FastAPI
│   │   ├── routes/
│   │   │   ├── extract.py      # Endpoints de extracción
│   │   │   ├── jobs.py         # Gestión de tareas
│   │   │   ├── history.py      # Historial de extracciones
│   │   │   ├── export.py       # Exportación de datos
│   │   │   └── templates.py    # Gestión de plantillas
│   │   └── schemas.py          # Modelos Pydantic
│   │
│   ├── cli/
│   │   ├── cli.py              # Interfaz de línea de comandos
│   │   ├── commands/
│   │   │   ├── extract.py      # Comando de extracción
│   │   │   ├── schedule.py     # Scheduling de tareas
│   │   │   ├── export.py       # Exportación
│   │   │   └── config.py       # Configuración
│   │   └── formatters.py       # Formateo de output
│   │
│   ├── web/
│   │   ├── app.vue             # Aplicación principal
│   │   ├── pages/
│   │   │   ├── Dashboard.vue   # Panel principal
│   │   │   ├── Extractor.vue   # Interfaz de extracción
│   │   │   ├── History.vue     # Historial
│   │   │   ├── Templates.vue   # Plantillas guardadas
│   │   │   └── Settings.vue
│   │   ├── components/
│   │   │   ├── UrlInput.vue
│   │   │   ├── DataPreview.vue
│   │   │   ├── FieldMapper.vue
│   │   │   └── ExportModal.vue
│   │   └── utils/
│   │
│   ├── models/
│   │   ├── extraction_job.py
│   │   ├── extraction_template.py
│   │   ├── extraction_history.py
│   │   └── export_config.py
│   │
│   ├── jobs/
│   │   ├── scheduler.py        # Celery scheduler
│   │   ├── tasks.py            # Tareas asíncronas
│   │   └── monitor.py          # Monitoreo de tareas
│   │
│   └── utils/
│       ├── validators.py
│       ├── rate_limiter.py
│       ├── proxy_handler.py
│       ├── error_handler.py
│       └── logging.py
│
├── tests/
│   ├── test_extractors.py
│   ├── test_scrapers.py
│   ├── test_api.py
│   ├── test_cli.py
│   ├── test_integration.py
│   └── fixtures/
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── USAGE.md
│   ├── API.md
│   ├── EXAMPLES.md
│   └── ADR/
│
├── examples/
│   ├── basic_html_extraction.py
│   ├── javascript_heavy_site.py
│   └── real_world_cases/
│
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
└── package.json
```

---

## 🏁 Comenzando

### Requisitos
- Python 3.11+
- Docker (opcional)

### Instalación
```bash
# Clonar el repositorio
git clone https://github.com/robertesteban/DataExtractor.git
cd DataExtractor

# Instalar dependencias
pip install -e .
```

### Uso vía CLI
```bash
python -m src.cli.cli extract "https://news.ycombinator.com" --type html
```

---

## 📄 Licencia
Distribuido bajo la Licencia MIT. Ver `LICENSE` para más información.
