import logging
from sqlalchemy import create_engine, text, event
from sqlalchemy.exc import (
    SQLAlchemyError, OperationalError, DatabaseError, TimeoutError
)
from sqlalchemy.pool import QueuePool
from src.scrapers.base_scraper import BaseScraper
from typing import List, Dict, Any
from urllib.parse import urlparse
import re

logger = logging.getLogger(__name__)

class DatabaseScraper(BaseScraper):
    # Bases de datos permitidas (whitelist)
    ALLOWED_HOSTS = ["localhost", "127.0.0.1", "db.internal.company.com"]
    ALLOWED_DIALECTS = ["postgresql", "mysql", "sqlite"]
    MAX_ROWS = 10000  # Límite de filas a extraer
    QUERY_TIMEOUT = 30  # Segundos
    
    def __init__(self):
        self.engines = {}  # Cache de engines
    
    def scrape(self, source: str, **kwargs) -> List[Dict[str, Any]]:
        """Ejecuta una query SQL de forma segura."""
        query = kwargs.get("query")
        
        if not query:
            raise ValueError("Se debe proporcionar una query SQL.")
        
        # Validaciones de seguridad
        self._validate_connection_string(source)
        self._validate_query(query)
        
        try:
            engine = self._get_engine(source)
            
            with engine.connect() as connection:
                # Agregar timeout
                connection.connection.timeout = self.QUERY_TIMEOUT
                
                logger.info(f"Ejecutando query en base de datos")
                result = connection.execute(text(query))
                
                # Limita a MAX_ROWS para evitar memory leaks
                rows = result.mappings().fetchmany(self.MAX_ROWS)
                data = [dict(row) for row in rows]
                
                logger.info(f"Query exitosa: {len(data)} filas extraídas")
                return data
        
        except OperationalError as e:
            logger.error(f"Error de conexión a base de datos: {e}")
            raise ValueError(f"No se pudo conectar a la base de datos: {str(e)}")
        
        except DatabaseError as e:
            logger.error(f"Error en query: {e}")
            raise ValueError(f"Error ejecutando query: {str(e)}")
        
        except TimeoutError:
            logger.error("Query excedió tiempo límite")
            raise TimeoutError(f"Query excedió {self.QUERY_TIMEOUT}s")
        
        except SQLAlchemyError as e:
            logger.error(f"Error SQLAlchemy: {e}")
            raise ValueError(f"Error en base de datos: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error inesperado: {e}", exc_info=True)
            raise ValueError(f"Error desconocido: {str(e)}")
    
    def _validate_connection_string(self, source: str) -> None:
        """Valida que la conexión sea segura."""
        try:
            parsed = urlparse(source)
        except Exception as e:
            raise ValueError(f"Connection string inválido: {e}")
        
        # 1. Validar dialecto
        dialect = parsed.scheme
        if dialect not in self.ALLOWED_DIALECTS:
            raise ValueError(f"Dialecto no permitido: {dialect}")
        
        # 2. Validar hostname (para no-SQLite)
        if dialect != "sqlite":
            hostname = parsed.hostname
            if hostname not in self.ALLOWED_HOSTS:
                raise ValueError(
                    f"Host no permitido: {hostname}. "
                    f"Hosts permitidos: {self.ALLOWED_HOSTS}"
                )
        
        logger.info(f"Connection string validado: {dialect}://{parsed.hostname}")
    
    def _validate_query(self, query: str) -> None:
        """Valida que la query sea segura (básico)."""
        query_upper = query.upper().strip()
        
        # Operaciones peligrosas
        dangerous_keywords = [
            "DROP", "DELETE FROM", "TRUNCATE", "ALTER",
            "CREATE", "INSERT", "UPDATE", "EXEC", "EXECUTE"
        ]
        
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                # Podría ser SELECT ... DROP ... como comentario, pero mejor ser strict
                logger.warning(f"Query contiene keyword sospechoso: {keyword}")
                raise ValueError(
                    f"Operación no permitida: {keyword}. "
                    "Solo se permiten queries SELECT."
                )
        
        # Validar que comienza con SELECT
        if not query_upper.startswith("SELECT"):
            raise ValueError("Solo se permiten queries SELECT para lectura.")
        
        # Detectar SQL injection básico
        if re.search(r"['\"]\s*(OR|AND)\s*['\"]?\s*1\s*=\s*1", query, re.IGNORECASE):
            raise ValueError("Posible SQL injection detectado.")
    
    def _get_engine(self, source: str):
        """Obtiene o crea un engine con pool de conexiones."""
        if source not in self.engines:
            logger.info(f"Creando nuevo engine para: {source}")
            
            # Configurar pool con límite de conexiones
            engine = create_engine(
                source,
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,  # Valida conexión antes de usar
                connect_args={"timeout": self.QUERY_TIMEOUT}
            )
            
            # Listener para log de conexiones
            @event.listens_for(engine, "connect")
            def receive_connect(dbapi_conn, connection_record):
                logger.debug("Nueva conexión a base de datos establecida")
            
            self.engines[source] = engine
        
        return self.engines[source]
    
    def close(self):
        """Cierra todos los engines."""
        for engine in self.engines.values():
            engine.dispose()
            logger.info("Engine cerrado y recursos liberados")
        self.engines.clear()
    
    def __del__(self):
        """Cleanup al destruir objeto."""
        self.close()