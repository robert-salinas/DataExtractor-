import logging
from typing import Dict, Type, Optional, Any, List
from abc import ABC, abstractmethod
from src.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class ScraperFactory:
    """
    Factory pattern para gestionar diferentes tipos de scrapers.
    Soporta registro dinámico, configuración, y singleton.
    """

    _instance = None  # Singleton
    _initialized = False

    def __new__(cls):
        """Patrón Singleton - una sola instancia."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Inicializar factory (solo una vez)."""
        if ScraperFactory._initialized:
            return

        self._scrapers: Dict[str, Type[BaseScraper]] = {}
        self._instances: Dict[str, BaseScraper] = {}
        self._config: Dict[str, Dict[str, Any]] = {}

        # Registrar scrapers por defecto
        self._register_default_scrapers()
        
        ScraperFactory._initialized = True
        logger.info("ScraperFactory inicializado")

    def _register_default_scrapers(self) -> None:
        """Registra los scrapers por defecto."""
        try:
            from src.scrapers.html_scraper import HTMLScraper
            self.register("html", HTMLScraper)
        except ImportError as e:
            logger.warning(f"No se pudo importar HTMLScraper: {e}")

        try:
            from src.scrapers.api_scraper import APIScraper
            self.register("api", APIScraper)
        except ImportError as e:
            logger.warning(f"No se pudo importar APIScraper: {e}")

        try:
            from src.scrapers.javascript_scraper import JSScraper
            self.register("spa", JSScraper)
            self.register("javascript", JSScraper)
        except ImportError as e:
            logger.warning(f"No se pudo importar JSScraper: {e}")

        try:
            from src.scrapers.pdf_scraper import PDFScraper
            self.register("pdf", PDFScraper)
        except ImportError as e:
            logger.warning(f"No se pudo importar PDFScraper: {e}")

        try:
            from src.scrapers.database_scraper import DatabaseScraper
            self.register("database", DatabaseScraper)
            self.register("db", DatabaseScraper)
        except ImportError as e:
            logger.warning(f"No se pudo importar DatabaseScraper: {e}")

        logger.info(f"Scrapers registrados: {', '.join(self._scrapers.keys())}")

    def register(
        self,
        scraper_type: str,
        scraper_class: Type[BaseScraper],
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Registra un nuevo tipo de scraper.
        
        Args:
            scraper_type: Identificador único del scraper
            scraper_class: Clase que hereda de BaseScraper
            config: Configuración por defecto para este scraper
        
        Raises:
            TypeError: Si scraper_class no hereda de BaseScraper
            ValueError: Si scraper_type está vacío
        """
        # Validaciones
        if not isinstance(scraper_type, str) or not scraper_type.strip():
            raise ValueError("scraper_type debe ser un string no vacío")

        if not issubclass(scraper_class, BaseScraper):
            raise TypeError(
                f"{scraper_class.__name__} debe heredar de BaseScraper"
            )

        scraper_type = scraper_type.strip().lower()

        # Registrar
        self._scrapers[scraper_type] = scraper_class
        if config:
            self._config[scraper_type] = config

        logger.info(f"Scraper registrado: {scraper_type} ({scraper_class.__name__})")

    def get_scraper(
        self,
        scraper_type: str,
        use_cache: bool = True,
        config: Optional[Dict[str, Any]] = None
    ) -> BaseScraper:
        """
        Obtiene una instancia de un scraper.
        
        Args:
            scraper_type: Tipo de scraper a obtener
            use_cache: Usar instancia cacheada (default: True)
            config: Configuración adicional para esta instancia
        
        Returns:
            Instancia de BaseScraper
        
        Raises:
            ValueError: Si el tipo de scraper no está registrado
        """
        # Validar entrada
        if not isinstance(scraper_type, str):
            raise ValueError("scraper_type debe ser un string")

        scraper_type = scraper_type.strip().lower()

        if not scraper_type:
            raise ValueError("scraper_type no puede estar vacío")

        # Validar que existe
        if scraper_type not in self._scrapers:
            available = self.get_available_scrapers()
            logger.error(
                f"Scraper no encontrado: {scraper_type}. "
                f"Disponibles: {available}"
            )
            raise ValueError(
                f"Tipo de scraper no soportado: '{scraper_type}'. "
                f"Disponibles: {', '.join(available)}"
            )

        # Usar cache si está habilitado
        if use_cache and scraper_type in self._instances:
            logger.debug(f"Retornando scraper cacheado: {scraper_type}")
            return self._instances[scraper_type]

        # Crear instancia
        scraper_class = self._scrapers[scraper_type]
        logger.debug(f"Creando nueva instancia: {scraper_type}")
        
        try:
            scraper = scraper_class()

            # Aplicar configuración por defecto
            if scraper_type in self._config:
                scraper.configure(**self._config[scraper_type])

            # Aplicar configuración adicional
            if config:
                scraper.configure(**config)

            # Cachear
            if use_cache:
                self._instances[scraper_type] = scraper

            logger.info(f"Scraper creado exitosamente: {scraper_type}")
            return scraper

        except Exception as e:
            logger.error(f"Error creando scraper {scraper_type}: {e}", exc_info=True)
            raise RuntimeError(
                f"No se pudo crear scraper '{scraper_type}': {str(e)}"
            )

    def get_available_scrapers(self) -> List[str]:
        """
        Retorna lista de tipos de scrapers disponibles.
        
        Returns:
            Lista de strings con tipos disponibles
        """
        return sorted(list(self._scrapers.keys()))

    def unregister(self, scraper_type: str) -> None:
        """
        Desregistra un tipo de scraper.
        
        Args:
            scraper_type: Tipo a desregistrar
        """
        scraper_type = scraper_type.strip().lower()

        if scraper_type in self._scrapers:
            del self._scrapers[scraper_type]
            
            # Limpiar instancia cacheada
            if scraper_type in self._instances:
                del self._instances[scraper_type]
            
            # Limpiar config
            if scraper_type in self._config:
                del self._config[scraper_type]

            logger.info(f"Scraper desregistrado: {scraper_type}")
        else:
            logger.warning(f"Scraper no encontrado para desregistrar: {scraper_type}")

    def clear_cache(self) -> None:
        """Limpia todas las instancias cacheadas."""
        self._instances.clear()
        logger.info("Cache de scrapers limpiado")

    def get_scraper_info(self, scraper_type: str) -> Dict[str, Any]:
        """
        Obtiene información de un scraper registrado.
        
        Args:
            scraper_type: Tipo de scraper
        
        Returns:
            Diccionario con información del scraper
        """
        scraper_type = scraper_type.strip().lower()

        if scraper_type not in self._scrapers:
            raise ValueError(f"Scraper no encontrado: {scraper_type}")

        scraper_class = self._scrapers[scraper_type]

        return {
            "type": scraper_type,
            "class": scraper_class.__name__,
            "module": scraper_class.__module__,
            "docstring": scraper_class.__doc__,
            "cached": scraper_type in self._instances,
            "config": self._config.get(scraper_type)
        }

    def list_scrapers(self) -> List[Dict[str, Any]]:
        """
        Retorna información de todos los scrapers registrados.
        
        Returns:
            Lista de diccionarios con información de cada scraper
        """
        return [
            self.get_scraper_info(scraper_type)
            for scraper_type in self.get_available_scrapers()
        ]

    def reset(self) -> None:
        """Resetea el factory a estado inicial."""
        self.clear_cache()
        self._scrapers.clear()
        self._config.clear()
        self._register_default_scrapers()
        logger.info("Factory reseteado")