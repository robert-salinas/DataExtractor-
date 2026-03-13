import logging
import httpx
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
import re
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

from src.scrapers.base_scraper import BaseScraper


class APIScraper(BaseScraper):
    """
    Scraper para APIs REST.
    Soporta múltiples métodos HTTP, autenticación, reintentos, y rate limiting.
    """

    # Configuración
    DEFAULT_TIMEOUT = 30.0
    MAX_RESPONSE_SIZE = 50 * 1024 * 1024  # 50MB
    MAX_RETRIES = 3
    RETRY_DELAY = 1
    
    # URLs permitidas (whitelist)
    ALLOWED_DOMAINS = [
        # Agregar dominios permitidos
    ]
    
    # Headers permitidos
    ALLOWED_HEADERS = {
        'Accept', 'Accept-Language', 'Accept-Encoding',
        'User-Agent', 'Authorization', 'Content-Type',
        'X-API-Key', 'X-Request-ID'
    }
    
    # Métodos HTTP permitidos
    ALLOWED_METHODS = {'GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD'}

    def __init__(self):
        """Inicializar scraper."""
        self.rate_limiter = RateLimiter()

    def scrape(self, source: str, **kwargs) -> List[Dict[str, Any]]:
        """
        Scrapeea una API.
        
        Args:
            source: URL del endpoint
            **kwargs:
                method: HTTP method (default: GET)
                headers: Dict de headers
                params: Query parameters
                json: Body JSON (para POST/PUT)
                auth_type: "bearer", "basic", "api_key"
                auth_value: Token/password/key
                fields: Campos a extraer
                selector: JSONPath o diccionario de selectores
                timeout: Timeout en segundos
        
        Returns:
            Lista de diccionarios con datos extraídos
        """
        method = kwargs.get("method", "GET").upper()
        headers = kwargs.get("headers", {})
        params = kwargs.get("params", {})
        json_body = kwargs.get("json")
        fields = kwargs.get("fields", [])
        selector = kwargs.get("selector")
        timeout = kwargs.get("timeout", self.DEFAULT_TIMEOUT)
        auth_type = kwargs.get("auth_type")
        auth_value = kwargs.get("auth_value")

        try:
            # 1. Validaciones
            self._validate_url(source)
            self._validate_method(method)
            headers = self._validate_headers(headers)
            
            # 2. Rate limiting
            self.rate_limiter.check_limit(source)

            # 3. Construir request
            request = self._build_request(
                source=source,
                method=method,
                headers=headers,
                params=params,
                json_body=json_body,
                auth_type=auth_type,
                auth_value=auth_value,
                timeout=timeout
            )

            # 4. Ejecutar request con reintentos
            response = self._fetch_with_retry(request)

            # 5. Parsear response
            data = self._parse_response(response)

            # 6. Extraer campos si es necesario
            if fields or selector:
                data = self._extract_fields(data, fields, selector)

            # 7. Convertir a formato estándar
            results = self._normalize_results(data)

            logger.info(f"API scraping exitoso: {len(results)} registros")
            return results

        except Exception as e:
            logger.error(f"Error en APIScraper: {e}")
            return [{"error": str(e)}]

    def _validate_url(self, url: str) -> None:
        """Valida que la URL sea segura."""
        try:
            parsed = urlparse(url)
        except Exception as e:
            raise ValueError(f"URL inválida: {e}")

        # Validar protocol
        if parsed.scheme not in ['http', 'https']:
            raise ValueError(f"Protocol no permitido: {parsed.scheme}")

        # Validar que no sea URL privada
        if self._is_private_url(parsed):
            raise ValueError(f"URL privada no permitida: {url}")

        # Validar dominio si hay whitelist
        if self.ALLOWED_DOMAINS:
            if parsed.netloc not in self.ALLOWED_DOMAINS:
                raise ValueError(f"Dominio no permitido: {parsed.netloc}")

        # Validar caracteres sospechosos
        if re.search(r'[<>"\'\`]', url):
            raise ValueError("URL contiene caracteres sospechosos")

    def _is_private_url(self, parsed) -> bool:
        """Verifica si es una URL privada."""
        private_patterns = [
            'localhost',
            '127.0.0.1',
            r'^192\.168\.',
            r'^10\.',
            r'^172\.(1[6-9]|2[0-9]|3[01])\.',
        ]

        hostname = parsed.hostname or ''
        return any(
            re.match(p, hostname) if isinstance(p, str) else p == hostname
            for p in private_patterns
        )

    def _validate_method(self, method: str) -> None:
        """Valida que el método HTTP sea permitido."""
        if method not in self.ALLOWED_METHODS:
            raise ValueError(
                f"Método no permitido: {method}. "
                f"Permitidos: {', '.join(self.ALLOWED_METHODS)}"
            )

    def _validate_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Valida y sanitiza headers."""
        if not isinstance(headers, dict):
            raise ValueError("Headers debe ser un diccionario")

        validated = {}
        
        for key, value in headers.items():
            # Validar key
            if key not in self.ALLOWED_HEADERS:
                logger.warning(f"Header no permitido ignorado: {key}")
                continue

            # Validar value
            if not isinstance(value, str):
                raise ValueError(f"Valor de header debe ser string: {key}")

            if len(value) > 1000:
                raise ValueError(f"Valor de header muy largo: {key}")

            # Sanitizar
            if '\n' in value or '\r' in value:
                raise ValueError(f"Header contiene saltos de línea: {key}")

            validated[key] = value

        return validated

    def _build_request(
        self,
        source: str,
        method: str,
        headers: Dict[str, str],
        params: Dict[str, Any],
        json_body: Optional[Dict],
        auth_type: Optional[str],
        auth_value: Optional[str],
        timeout: float
    ) -> Dict[str, Any]:
        """Construye el request con todas las validaciones."""
        
        request = {
            "method": method,
            "url": source,
            "headers": headers.copy(),
            "timeout": timeout,
        }

        # Agregar params si hay
        if params:
            if not isinstance(params, dict):
                raise ValueError("params debe ser un diccionario")
            request["params"] = params

        # Agregar body si hay
        if json_body is not None:
            if method not in ['POST', 'PUT', 'PATCH']:
                raise ValueError(f"No se puede enviar body con {method}")
            request["json"] = json_body

        # Agregar autenticación
        if auth_type and auth_value:
            request["headers"].update(
                self._build_auth_header(auth_type, auth_value)
            )

        return request

    def _build_auth_header(
        self,
        auth_type: str,
        auth_value: str
    ) -> Dict[str, str]:
        """Construye header de autenticación."""
        auth_type = auth_type.lower()

        if auth_type == 'bearer':
            # Validar que sea un token válido
            if not re.match(r'^[a-zA-Z0-9\.\-_]+$', auth_value):
                raise ValueError("Token Bearer inválido")
            return {"Authorization": f"Bearer {auth_value}"}

        elif auth_type == 'basic':
            import base64
            # Validar que sea user:pass
            if ':' not in auth_value:
                raise ValueError("Credenciales basic deben ser user:password")
            encoded = base64.b64encode(auth_value.encode()).decode()
            return {"Authorization": f"Basic {encoded}"}

        elif auth_type == 'api_key':
            # Validar que sea un key válido
            if not auth_value or len(auth_value) < 10:
                raise ValueError("API Key inválida")
            return {"X-API-Key": auth_value}

        else:
            raise ValueError(f"Tipo de auth no soportado: {auth_type}")

    def _fetch_with_retry(
        self,
        request: Dict[str, Any],
        attempt: int = 0
    ) -> httpx.Response:
        """Fetch con reintentos automáticos."""
        try:
            logger.debug(f"Request attempt {attempt + 1}/{self.MAX_RETRIES}")
            
            with httpx.Client(timeout=request["timeout"]) as client:
                response = client.request(**request)

                # Validar status code
                if response.status_code in [429, 502, 503, 504]:
                    # Reintentar en estos casos
                    if attempt < self.MAX_RETRIES - 1:
                        delay = (2 ** attempt) + (attempt * self.RETRY_DELAY)
                        logger.warning(
                            f"Status {response.status_code}, "
                            f"reintentando en {delay}s"
                        )
                        import asyncio
                        import time
                        time.sleep(delay)
                        return self._fetch_with_retry(request, attempt + 1)

                # Para otros 4xx, no reintentar
                if 400 <= response.status_code < 500:
                    try:
                        error_data = response.json()
                        error_msg = error_data.get("message", str(error_data))
                    except:
                        error_msg = response.text[:200]
                    
                    raise ValueError(
                        f"HTTP {response.status_code}: {error_msg}"
                    )

                response.raise_for_status()
                return response

        except httpx.TimeoutException:
            if attempt < self.MAX_RETRIES - 1:
                delay = (2 ** attempt) + (attempt * self.RETRY_DELAY)
                logger.warning(f"Timeout, reintentando en {delay}s")
                import time
                time.sleep(delay)
                return self._fetch_with_retry(request, attempt + 1)
            raise TimeoutError(f"Request timeout después de {self.MAX_RETRIES} intentos")

        except httpx.RequestError as e:
            logger.error(f"Request error: {e}")
            raise

    def _parse_response(self, response: httpx.Response) -> Any:
        """Parsea el response."""
        
        # Validar tamaño
        if len(response.content) > self.MAX_RESPONSE_SIZE:
            raise ValueError(
                f"Response demasiado grande: {len(response.content)} bytes"
            )

        # Determinar tipo de contenido
        content_type = response.headers.get('content-type', '').lower()

        try:
            if 'application/json' in content_type:
                return response.json()
            elif 'text/csv' in content_type:
                return self._parse_csv(response.text)
            elif 'text/xml' in content_type or 'application/xml' in content_type:
                return self._parse_xml(response.text)
            else:
                # Intentar JSON igual
                try:
                    return response.json()
                except:
                    return [{"content": response.text}]

        except Exception as e:
            logger.error(f"Error parseando response: {e}")
            return [{"content": response.text}]

    def _parse_csv(self, text: str) -> List[Dict]:
        """Parsea CSV."""
        import csv
        from io import StringIO

        reader = csv.DictReader(StringIO(text))
        return list(reader)

    def _parse_xml(self, text: str) -> List[Dict]:
        """Parsea XML (básico)."""
        import xml.etree.ElementTree as ET

        root = ET.fromstring(text)
        result = []

        for element in root:
            item = {}
            for child in element:
                item[child.tag] = child.text
            if item:
                result.append(item)

        return result if result else [{"xml": text}]

    def _extract_fields(
        self,
        data: Any,
        fields: List[str],
        selector: Optional[Dict[str, str]]
    ) -> Any:
        """Extrae campos específicos."""
        
        # Si data es lista
        if isinstance(data, list):
            return [
                self._extract_from_object(item, fields, selector)
                for item in data
            ]
        
        # Si data es diccionario
        return [self._extract_from_object(data, fields, selector)]

    def _extract_from_object(
        self,
        obj: Dict,
        fields: List[str],
        selector: Optional[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Extrae campos de un objeto."""
        result = {}

        for field in fields:
            # Usar selector si existe
            if selector and field in selector:
                path = selector[field]
                value = self._get_nested_value(obj, path)
            else:
                # Búsqueda simple
                value = obj.get(field)

            result[field] = value

        return result

    def _get_nested_value(self, obj: Dict, path: str) -> Any:
        """Obtiene valor anidado usando dot notation."""
        try:
            parts = path.split('.')
            value = obj

            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    return None

                if value is None:
                    return None

            return value
        except:
            return None

    def _normalize_results(self, data: Any) -> List[Dict[str, Any]]:
        """Convierte resultado a formato estándar."""
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            return [data]
        else:
            return [{"value": data}]


class RateLimiter:
    """Control de rate limiting por dominio."""

    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests = {}

    def check_limit(self, url: str) -> None:
        """Verifica si se ha excedido el rate limit."""
        from urllib.parse import urlparse

        domain = urlparse(url).netloc
        now = datetime.now()

        if domain not in self.requests:
            self.requests[domain] = []

        # Limpiar requests antiguos (> 1 minuto)
        self.requests[domain] = [
            req_time for req_time in self.requests[domain]
            if now - req_time < timedelta(minutes=1)
        ]

        # Verificar límite
        if len(self.requests[domain]) >= self.requests_per_minute:
            raise ValueError(
                f"Rate limit excedido para {domain}. "
                f"Máximo: {self.requests_per_minute} por minuto"
            )

        # Registrar request
        self.requests[domain].append(now)