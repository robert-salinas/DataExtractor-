# RS DataExtractor

> Herramienta OSINT y extracción de datos de grado industrial.

RS DataExtractor es una plataforma avanzada diseñada para la recolección, análisis y auditoría de datos en entornos web y de red. Combina capacidades de evasión de protecciones modernas con motores de detección de vulnerabilidades y extracción OSINT.

## Capacidades

- **Dashboard Profesional**: Interfaz moderna con navegación lateral, tarjetas de KPI en tiempo real y paneles duales para visualización de resultados.
- **Web Scraping Avanzado**: Evasión de Cloudflare y protecciones antibot mediante Playwright en modo stealth (non-headless) con rotación de proxies por contexto. Soporte para HTML, JS, PDF y bases de datos.
- **OSINT Completo**: Enumeración de subdominios (crt.sh con filtrado de wildcards), registros DNS exhaustivos (A, MX, TXT, NS, SOA, AAAA, SPF, DMARC) y verificación de brechas de seguridad (LeakCheck).
- **Historial y Persistencia**: Sistema de gestión de resultados previos con capacidad de carga, restauración y limpieza, integrado con SQLite.
- **Configuración Dinámica**: Panel de ajustes en tiempo real para scraping, proxies y parámetros OSINT con persistencia en YAML.
- **SQLi Probe**: Motor de detección de inyecciones SQL (error-based y time-based) con baseline dinámico, soporte para parámetros GET/POST y headers (X-Forwarded-For, User-Agent, Referer).
- **Deobfuscation Engine**: Decodificación robusta de Base64 (con validación de entropía), Hex, y strings ofuscadas en JavaScript (Array Joins, CharCodes).
- **API REST**: Interfaz programática completa en `localhost:8000` con FastAPI para integración con otras herramientas.

## Testing Automatizado

El proyecto incluye una suite de pruebas robusta basada en **PyAutoGUI** y **Subprocess** para simular interacciones reales de usuario:

1. **Ejecución de Tests**:
   ```bash
   python test_suite.py
   ```
2. **Cobertura de Pruebas**:
   - Validación de arranque y detección de ventanas.
   - Reactividad de la interfaz ante URL, Email, IP y HTML.
   - Flujos completos de Scraping y OSINT.
   - Verificación de detención de procesos (Botón STOP) y limpieza de zombies.
   - Pruebas de exportación de datos y persistencia del historial.
   - Integración y salud de la API REST.

3. **Reportes**: Generación automática de `reporte_tests.html` con estados Pass/Fail, tiempos de ejecución y **evidencia visual (screenshots)** embebida en Base64.

## Instalación rápida

1. **Doble click en `start.bat`**: El lanzador centralizado del proyecto.
2. **Opción 3 — Instalar dependencias**: Configura el entorno Python y descarga los binarios necesarios (Playwright, etc.).
3. **Opción 1 — Iniciar GUI**: Lanza la interfaz gráfica profesional construida con CustomTkinter.

## Uso de la API

Inicie el servicio desde el menú principal:
1. Ejecutar `start.bat` -> **Opción 2**.
2. Acceda a la documentación interactiva en: [http://localhost:8000/docs](http://localhost:8000/docs)

## Configuración

Toda la lógica del sistema es personalizable a través de `config.yaml`. No se utilizan valores hardcodeados:
- **Scraping**: Rate limits, reintentos, timeouts y modo headless.
- **Proxies**: Configuración de archivos y rotación automática.
- **OSINT**: Tipos de registros DNS y límites de subdominios.
- **SQLi**: Multiplicadores de umbral para ataques time-based y selección de vectores de ataque.
- **Exportación**: Formatos (JSON/CSV) y rutas de salida.

## Estructura del Proyecto

```text
RS-DataExtractor/
├── main.py                 # Punto de entrada principal
├── test_suite.py           # Suite de tests UI (PyAutoGUI)
├── service.bat             # Ejecutor para API Service
├── start.bat               # Lanzador interactivo
├── src/
│   ├── desktop/
│   │   ├── ui.py           # Dashboard (CustomTkinter)
│   │   └── logic/
│   │       ├── config_manager.py  # Gestor YAML (Singleton)
│   │       ├── detector.py        # RS Brain (Clasificador)
│   │       ├── db.py              # Gestión SQLite
│   │       ├── osint.py           # Pipeline OSINT
│   │       ├── sqli.py            # Engine de auditoría SQLi
│   │       └── thread_manager.py  # Control de concurrencia
│   ├── scrapers/           # Fábrica y motores de extracción
│   │   ├── scraper_factory.py
│   │   └── ... (HTML, JS, PDF, API, DB)
│   └── api/
│       ├── main.py         # Entrypoint FastAPI
│       └── server.py       # Lógica del servidor
└── results/                # Exportaciones y capturas de test
```

## Distribución

Para generar un ejecutable independiente para Windows:
```bash
build.bat
```
El resultado se encontrará en la carpeta `dist/RSDataExtractor.exe`.
