# Solución de Problemas 🛠️

## Errores Comunes

### 1. Error al conectar con Redis
**Síntoma:** Los jobs de Celery no se inician.
**Solución:** Asegúrate de que el contenedor de Redis esté corriendo (`docker ps`) o que la URL en `.env` sea correcta.

### 2. Playwright no encuentra el navegador
**Síntoma:** Error al intentar scrapear sitios SPA.
**Solución:** Ejecuta `playwright install` para descargar los binarios de los navegadores necesarios.

### 3. Dependencias de PostgreSQL
**Síntoma:** Error al instalar `psycopg2`.
**Solución:** Asegúrate de tener instaladas las librerías de desarrollo de Postgres en tu sistema operativo.

---
Para más ayuda, abre un Issue en el repositorio.
