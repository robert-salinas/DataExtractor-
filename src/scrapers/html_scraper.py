import httpx
import logging
from bs4 import BeautifulSoup
from src.scrapers.base_scraper import BaseScraper
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import re
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

@dataclass
class FieldSelector:
    """Define cómo extraer un campo"""
    name: str
    selector: Optional[str] = None
    attribute: str = "text"  # "text", "href", "src", "data-*"
    required: bool = False

class HTMLScraper(BaseScraper):
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self.client = httpx.Client(timeout=10.0, follow_redirects=True)
    
    def scrape(self, source: str, **kwargs) -> List[Dict[str, Any]]:
        """Extrae datos estructurados de una página HTML."""
        fields = kwargs.get("fields", [])
        selectors = kwargs.get("selectors", {})
        container_selector = kwargs.get("container_selector")
        
        try:
            if not self._is_safe_public_url(source):
                raise ValueError("URL no permitida (SSRF bloqueado)")
            html = self._fetch_with_retry(source)
            soup = BeautifulSoup(html, "html.parser")
            
            # Detectar contenedores automáticamente o usar selector especificado
            containers = self._find_containers(soup, container_selector)
            
            results = []
            for container in containers:
                extracted_item = self._extract_fields(container, fields, selectors)
                if extracted_item:
                    results.append(extracted_item)
            
            logger.info(f"Extracción exitosa: {len(results)} registros de {source}")
            return results if results else [{"error": "No se encontraron datos"}]
            
        except httpx.HTTPError as e:
            logger.error(f"Error HTTP: {e}")
            return [{"error": f"Error HTTP: {e.response.status_code}"}]
        except Exception as e:
            logger.error(f"Error en extracción: {e}")
            return [{"error": str(e)}]
    
    def _is_safe_public_url(self, url: str) -> bool:
        """Valida que la URL no apunte a hosts privados o locales."""
        try:
            parsed = urlparse(url)
            if parsed.scheme not in ("http", "https"):
                return False
            host = parsed.hostname or ""
            if host in {"localhost", "127.0.0.1"}:
                return False
            private_patterns = [
                r"^10\.\d+\.\d+\.\d+$",
                r"^192\.168\.\d+\.\d+$",
                r"^172\.(1[6-9]|2\d|3[0-1])\.\d+\.\d+$",
            ]
            for pat in private_patterns:
                if re.match(pat, host or ""):
                    return False
            return True
        except Exception:
            return False
    
    def _fetch_with_retry(self, url: str, attempt: int = 0) -> str:
        """Obtiene HTML con reintentos automáticos."""
        try:
            response = self.client.get(url)
            response.raise_for_status()
            return response.text
        except httpx.TimeoutException:
            if attempt < self.max_retries - 1:
                logger.warning(f"Timeout en {url}, reintentando... ({attempt + 1}/{self.max_retries})")
                return self._fetch_with_retry(url, attempt + 1)
            raise
        except httpx.HTTPError as e:
            logger.error(f"Error HTTP en {url}: {e}")
            raise
    
    def _find_containers(self, soup: BeautifulSoup, selector: Optional[str]) -> list:
        """Encuentra contenedores de datos."""
        if selector:
            return soup.select(selector)
        
        # Heurística: detectar patrones comunes
        common_selectors = [
            "article",
            "div.item",
            "div.product",
            "li",
            "tr"  # Para tablas
        ]
        
        for sel in common_selectors:
            containers = soup.select(sel)
            if len(containers) > 1:  # Si hay múltiples, es probable que sea correcto
                logger.debug(f"Detectados {len(containers)} contenedores con '{sel}'")
                return containers
        
        # Fallback: retorna el body completo
        return [soup.body] if soup.body else [soup]
    
    def _extract_fields(self, container: BeautifulSoup, fields: List[str], 
                       selectors: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Extrae campos de un contenedor."""
        extracted = {}
        
        for field in fields:
            value = self._extract_field_value(container, field, selectors)
            extracted[field] = value
        
        # Solo retorna si tiene al menos un campo válido
        if any(v is not None for v in extracted.values()):
            return extracted
        return None
    
    def _extract_field_value(self, container: BeautifulSoup, field: str, 
                            selectors: Dict[str, str]) -> Optional[str]:
        """Extrae valor de un campo con múltiples estrategias."""
        
        # 1. Selector CSS explícito
        if field in selectors and selectors[field]:
            element = container.select_one(selectors[field])
            if element:
                return self._get_element_value(element)
        
        # 2. Búsqueda por ID
        element = container.find(id=field)
