from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from enum import Enum
import logging
from datetime import datetime
from dataclasses import dataclass

# ============================================================================
# EXCEPCIONES PERSONALIZADAS
# ============================================================================

class ScraperError(Exception):
    """Base exception for all scraper errors"""
    pass

class SourceAccessError(ScraperError):
    """No se pudo acceder a la fuente"""
    pass

class ValidationError(ScraperError):
    """Validación de parámetros falló"""
    pass

class TimeoutError(ScraperError):
    """La operación excedió el timeout"""
    pass

class UnsupportedSourceError(ScraperError):
    """Tipo de fuente no soportado"""
    pass

# ============================================================================
# ENUMS Y TIPOS
# ============================================================================

class SourceType(str, Enum):
    """Tipos de fuentes soportadas"""
    HTML = "html"
    JSON = "json"
    CSV = "csv"
    DATABASE = "database"
    XML = "xml"

@dataclass
class ScraperMetadata:
    """Metadata de un scraper"""
    name: str
    version: str
    supported_types: List[SourceType]
    description: str
    author: Optional[str] = None
    max_timeout: int = 300  # segundos

# ============================================================================
# BASE SCRAPER ABSTRACTO
# ============================================================================

class BaseScraper(ABC):
    """
    Abstract base class para todos los scrapers.
    
    Proporciona interfaz consistente y validaciones comunes.
    
    Subclases deben implementar:
        - scrape()
        - validate_source()
        - get_metadata()
    
    Ejemplo:
        >>> class HTMLScraper(BaseScraper):
        ...     def scrape(self, source, **kwargs):
        ...         # Implementar
        ...         pass
        ...     
        ...     def validate_source(self, source):
        ...         return source.startswith('http')
        ...     
        ...     def get_metadata(self):
        ...         return ScraperMetadata(...)
        
        >>> scraper = HTMLScraper()
        >>> with scraper:
        ...     results = scraper.scrape('https://example.com')
    """

    def __init__(self, timeout: int = 30, enable_logging: bool = True):
        """
        Inicializar scraper.
        
        Args:
            timeout: Timeout por defecto en segundos
            enable_logging: Habilitar logging automático
        """
        self._timeout = timeout
        self._initialized = True
        
        # Configurar logger
        self.logger = logging.getLogger(self.__class__.__name__)
        if enable_logging:
            self._setup_logging()
        
        self.logger.debug(f"Scraper inicializado: {self.__class__.__name__}")
    
    def _setup_logging(self):
        """Configurar logger"""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    # ========================================================================
    # MÉTODOS ABSTRACTOS
    # ========================================================================
    
    @abstractmethod
    def scrape(self, source: str, **kwargs) -> List[Dict[str, Any]]:
        """
        Extrae datos de una fuente.
        
        Args:
            source: URL, ruta de archivo, o conexión a la fuente
            **kwargs: Parámetros específicos del scraper
                fields (List[str]): Campos a extraer
                selectors (Dict[str, str]): Selectores CSS/XPath
                timeout (int): Timeout en segundos (overrides default)
                options (Dict): Opciones adicionales específicas
        
        Returns:
            List[Dict[str, Any]]: Lista de registros extraídos
            
        Raises:
            ValidationError: Si los parámetros son inválidos
            SourceAccessError: Si no se puede acceder a la fuente
            TimeoutError: Si se excede el timeout
            ScraperError: Para otros errores de scraping
        
        Examples:
            >>> scraper = HTMLScraper()
            >>> data = scraper.scrape(
            ...     'https://example.com',
            ...     fields=['title', 'price'],
            ...     selectors={'title': 'h1', 'price': '.price'}
            ... )
            >>> print(len(data))
            42
        """
        pass
    
    @abstractmethod
    def validate_source(self, source: str) -> bool:
        """
        Valida que la fuente sea accesible y válida.
        
        Args:
            source: Fuente a validar
        
        Returns:
            bool: True si es válida
        
        Raises:
            ValidationError: Si la validación falla
        """
        pass
    
    @abstractmethod
    def get_metadata(self) -> ScraperMetadata:
        """
        Retorna metadata del scraper.
        
        Returns:
            ScraperMetadata: Información del scraper
        """
        pass
    
    # ========================================================================
    # MÉTODOS CONCRETOS
    # ========================================================================
    
    def get_name(self) -> str:
        """Obtener nombre del scraper"""
        return self.get_metadata().name
    
    def get_supported_types(self) -> List[SourceType]:
        """Obtener tipos soportados"""
        return self.get_metadata().supported_types
    
    def supports_type(self, source_type: SourceType) -> bool:
        """Verificar si soporta un tipo"""
        return source_type in self.get_supported_types()
    
    def get_timeout(self) -> int:
        """Obtener timeout configurado"""
        return self._timeout
    
    def set_timeout(self, timeout: int) -> None:
        """Establecer timeout"""
        if timeout <= 0:
            raise ValidationError("Timeout debe ser positivo")
        self._timeout = timeout
        self.logger.debug(f"Timeout establecido a {timeout}s")
    
    def _validate_result(self, result: Any) -> None:
        """
        Valida que el resultado sea válido.
        
        Args:
            result: Resultado a validar
        
        Raises:
            ValidationError: Si el resultado no es válido
        """
        if not isinstance(result, list):
            raise ValidationError(
                f"Resultado debe ser lista, recibido {type(result).__name__}"
            )
        
        if result:  # Si no está vacío
            if not isinstance(result[0], dict):
                raise ValidationError(
                    f"Elementos deben ser dict, recibido {type(result[0]).__name__}"
                )
            
            # Validar que no haya valores None sospechosos
            for item in result:
                if not isinstance(item, dict):
                    raise ValidationError(f"Elemento no es dict: {item}")
    
    def _validate_kwargs(self, kwargs: Dict[str, Any], 
                        required: List[str] = None,
                        optional: List[str] = None) -> None:
        """
        Valida kwargs contra lista blanca.
        
        Args:
            kwargs: Kwargs a validar
            required: Claves requeridas
            optional: Claves opcionales permitidas
        
        Raises:
            ValidationError: Si hay claves inválidas
        """
        allowed = set()
        if required:
            allowed.update(required)
        if optional:
            allowed.update(optional)
        
        invalid = set(kwargs.keys()) - allowed
        if invalid:
            raise ValidationError(f"Parámetros inválidos: {invalid}")
        
        if required:
            missing = set(required) - set(kwargs.keys())
            if missing:
                raise ValidationError(f"Parámetros requeridos faltantes: {missing}")
    
    # ========================================================================
    # CONTEXT MANAGER
    # ========================================================================
    
    def __enter__(self):
        """Soporte para 'with' statement"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanup al salir de 'with'"""
        self.close()
        return False
    
    def close(self) -> None:
        """
        Cierra recursos (override en subclases si es necesario).
        
        Este método se llama automáticamente al salir de un 'with' statement.
        """
        self.logger.debug(f"Scraper cerrado: {self.__class__.__name__}")
    
    # ========================================================================
    # UTILIDADES
    # ========================================================================
    
    def log_extraction(self, source: str, record_count: int, 
                      duration_ms: float) -> None:
        """Log de extracción exitosa"""
        self.logger.info(
            f"Extracción exitosa: {record_count} registros en {duration_ms:.2f}ms"
        )
    
    def log_error(self, error: Exception, source: str) -> None:
        """Log de error de extracción"""
        self.logger.error(
            f"Error en extracción: {error.__class__.__name__}: {str(error)}",
            exc_info=True
        )
    
    def __repr__(self) -> str:
        """Representación string"""
        return f"{self.__class__.__name__}(timeout={self._timeout}s)"