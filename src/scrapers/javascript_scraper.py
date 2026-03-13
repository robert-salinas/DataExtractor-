import asyncio
import logging
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from src.scrapers.base_scraper import BaseScraper
import json

logger = logging.getLogger(__name__)

try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
except ImportError:
    raise ImportError(
        "Playwright no está instalado. Instala con: pip install playwright\n"
        "Luego ejecuta: playwright install"
    )


class JSScraper(BaseScraper):
    """
    Scraper para sitios con contenido renderizado por JavaScript.
    Usa Playwright para automatización del navegador.
    """

    # Configuración
    BROWSER_TIMEOUT = 30000  # 30 segundos
    PAGE_LOAD_TIMEOUT = 30000
    MAX_RETRIES = 2
    VIEWPORT = {"width": 1280, "height": 720}
    
    # User Agent realista
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    def scrape(self, source: str, **kwargs) -> List[Dict[str, Any]]:
        """
        Renderiza y extrae datos de una página con JavaScript.
        
        Args:
            source: URL a scrapear
            **kwargs:
                fields: Lista de campos a extraer
                selectors: Dict de selectores CSS
                wait_for: Selector o timeout para esperar
                container_selector: Selector para contenedores
        
        Returns:
            Lista de dictionaries con datos extraídos
        """
        fields = kwargs.get("fields", [])
        selectors = kwargs.get("selectors", {})
        wait_for = kwargs.get("wait_for")
        container_selector = kwargs.get("container_selector")

        try:
            # Ejecutar en loop async
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            results = loop.run_until_complete(
                self._scrape_async(
                    source=source,
                    fields=fields,
                    selectors=selectors,
                    wait_for=wait_for,
                    container_selector=container_selector
                )
            )
            
            return results

        except Exception as e:
            logger.error(f"Error en JSScraper: {e}")
            return [{"error": str(e)}]
        
        finally:
            loop.close()

    async def _scrape_async(
        self,
        source: str,
        fields: List[str],
        selectors: Dict[str, str],
        wait_for: Optional[str] = None,
        container_selector: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Scraping asincrónico con Playwright."""
        
        async with async_playwright() as p:
            browser = await self._launch_browser(p)
            
            try:
                context = await browser.new_context(
                    viewport=self.VIEWPORT,
                    user_agent=self.USER_AGENT,
                    ignore_https_errors=True  # Para HTTPS sin certificado
                )

                page = await context.new_page()

                try:
                    # 1. Navegar a la página
                    logger.info(f"Navegando a {source}")
                    await self._goto_page(page, source)

                    # 2. Esperar a que cargue contenido (si es necesario)
                    if wait_for:
                        await self._wait_for_content(page, wait_for)
                    
                    # 3. Inyectar scripts si es necesario
                    await self._inject_scripts(page)

                    # 4. Obtener contenido renderizado
                    html = await page.content()

                    # 5. Parsear y extraer datos
                    soup = BeautifulSoup(html, "html.parser")
                    results = self._extract_data(
                        soup=soup,
                        fields=fields,
                        selectors=selectors,
                        container_selector=container_selector
                    )

                    logger.info(f"Extracción exitosa: {len(results)} registros")
                    return results

                finally:
                    await page.close()
                    await context.close()

            finally:
                await browser.close()

    async def _launch_browser(self, p):
        """Lanza el navegador con configuración óptima."""
        try:
            logger.debug("Lanzando navegador Chromium")
            
            browser = await p.chromium.launch(
                headless=True,  # Modo headless (sin GUI)
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',  # Para sistemas con poco /dev/shm
                ]
            )
            
            return browser
        except Exception as e:
            logger.error(f"Error lanzando navegador: {e}")
            raise RuntimeError(
                "No se pudo lanzar Playwright. "
                "Ejecuta: playwright install chromium"
            )

    async def _goto_page(self, page, url: str, retries: int = 0):
        """Navega a la página con reintentos."""
        try:
            await page.goto(
                url,
                wait_until="networkidle",  # Espera a que la red esté inactiva
                timeout=self.PAGE_LOAD_TIMEOUT
            )
            logger.debug(f"Página cargada: {url}")

        except PlaywrightTimeoutError:
            if retries < self.MAX_RETRIES:
                logger.warning(f"Timeout cargando {url}, reintentando...")
                await asyncio.sleep(2)
                return await self._goto_page(page, url, retries + 1)
            raise TimeoutError(f"Timeout cargando {url} después de {self.MAX_RETRIES} reintentos")

        except Exception as e:
            logger.error(f"Error navegando a {url}: {e}")
            raise

    async def _wait_for_content(self, page, wait_for: str):
        """Espera a que un elemento o timeout ocurra."""
        try:
            # Si es un número, es un timeout en ms
            if wait_for.isdigit():
                timeout = int(wait_for)
                logger.debug(f"Esperando {timeout}ms")
                await page.wait_for_timeout(timeout)
            else:
                # Si es un selector, espera a que aparezca
                logger.debug(f"Esperando selector: {wait_for}")
                await page.wait_for_selector(wait_for, timeout=self.BROWSER_TIMEOUT)

        except PlaywrightTimeoutError:
            logger.warning(f"Timeout esperando por: {wait_for}")
            # No lanzar error, continuar de todas formas

    async def _inject_scripts(self, page):
        """Inyecta scripts útiles (scroll, close ads, etc)."""
        try:
            # Script para hacer scroll y cargar contenido lazy
            await page.evaluate("""
                async () => {
                    // Scroll hasta el final
                    let previousHeight = document.body.scrollHeight;
                    while (true) {
                        window.scrollBy(0, window.innerHeight);
                        await new Promise(resolve => setTimeout(resolve, 500));
                        
                        let newHeight = document.body.scrollHeight;
                        if (newHeight === previousHeight) break;
                        previousHeight = newHeight;
                    }
                    
                    // Volver al top
                    window.scrollTo(0, 0);
                }
            """)
            logger.debug("Scripts inyectados exitosamente")

        except Exception as e:
            logger.warning(f"Error inyectando scripts: {e}")
            # No es crítico, continuar

    def _extract_data(
        self,
        soup: BeautifulSoup,
        fields: List[str],
        selectors: Dict[str, str],
        container_selector: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Extrae datos del HTML parseado."""
        
        # Encontrar contenedores
        if container_selector:
            containers = soup.select(container_selector)
            logger.debug(f"Encontrados {len(containers)} contenedores")
        else:
            # Detectar automáticamente
            containers = self._detect_containers(soup)

        results = []
        for container in containers:
            item = {}
            
            for field in fields:
                value = self._extract_field(container, field, selectors)
                item[field] = value

            # Solo incluir si tiene al menos un campo válido
            if any(v is not None for v in item.values()):
                results.append(item)

        return results

    def _extract_field(
        self,
        container: BeautifulSoup,
        field: str,
        selectors: Dict[str, str]
    ) -> Optional[str]:
        """Extrae un campo específico."""
        
        # 1. Selector CSS explícito
        if field in selectors and selectors[field]:
            try:
                element = container.select_one(selectors[field])
                if element:
                    return element.get_text(strip=True)
            except Exception as e:
                logger.debug(f"Error con selector {field}: {e}")

        # 2. Búsqueda por ID
        element = container.find(id=field)
        if element:
            return element.get_text(strip=True)

        # 3. Búsqueda por clase
        element = container.find(class_=field)
        if element:
            return element.get_text(strip=True)

        # 4. Búsqueda por atributo data-*
        element = container.find(attrs={f"data-{field}": True})
        if element:
            return element.get(f"data-{field}")

        return None

    def _detect_containers(self, soup: BeautifulSoup) -> list:
        """Detecta automáticamente contenedores de datos."""
        
        common_patterns = [
            ("div", {"class": lambda x: x and "item" in x}),
            ("div", {"class": lambda x: x and "product" in x}),
            ("article", {}),
            ("li", {}),
            ("tr", {}),
        ]

        for tag, attrs in common_patterns:
            elements = soup.find_all(tag, attrs, limit=50)
            if len(elements) > 1:
                logger.debug(f"Detectados {len(elements)} contenedores con patrón {tag}")
                return elements

        # Fallback: retorna el body
        return [soup.body] if soup.body else [soup]