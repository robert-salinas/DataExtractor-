import logging
import os
import httpx
from io import BytesIO
from typing import List, Dict, Any, Optional
from pathlib import Path
from PyPDF2 import PdfReader
from PyPDF2.errors import PdfReadError
import re

logger = logging.getLogger(__name__)

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False
    logger.warning("pdfplumber no instalado. Instala con: pip install pdfplumber")

from src.scrapers.base_scraper import BaseScraper


class PDFScraper(BaseScraper):
    """
    Scraper para archivos PDF.
    Extrae texto, tablas y campos específicos.
    """

    # Configuración
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    DOWNLOAD_TIMEOUT = 30
    MAX_PAGES = 500
    
    # Rutas permitidas (para seguridad)
    ALLOWED_PATHS = [
        os.path.expanduser("~/downloads"),
        os.path.expanduser("~/documents"),
        "/tmp",
    ]

    def scrape(self, source: str, **kwargs) -> List[Dict[str, Any]]:
        """
        Extrae datos de un PDF.
        
        Args:
            source: Ruta local o URL del PDF
            **kwargs:
                fields: Campos a extraer
                extract_tables: Extraer tablas (default: True)
                extract_images: Extraer metadatos de imágenes
                search_text: Buscar texto específico
                ocr: Usar OCR para PDFs escaneados (requiere tesseract)
        
        Returns:
            Lista de dictionaries con datos extraídos
        """
        fields = kwargs.get("fields", [])
        extract_tables = kwargs.get("extract_tables", True)
        search_text = kwargs.get("search_text")
        use_ocr = kwargs.get("ocr", False)

        try:
            # 1. Obtener archivo PDF
            pdf_content = self._get_pdf_content(source)
            
            # 2. Validar PDF
            self._validate_pdf(pdf_content)
            
            # 3. Parsear PDF
            results = self._parse_pdf(
                pdf_content=pdf_content,
                fields=fields,
                extract_tables=extract_tables,
                search_text=search_text,
                use_ocr=use_ocr
            )

            logger.info(f"PDF extracción exitosa: {len(results)} registros")
            return results

        except Exception as e:
            logger.error(f"Error en PDFScraper: {e}")
            return [{"error": str(e)}]

    def _get_pdf_content(self, source: str) -> bytes:
        """Obtiene contenido del PDF desde archivo o URL."""
        
        # URL
        if source.startswith(('http://', 'https://')):
            logger.info(f"Descargando PDF desde URL: {source}")
            return self._download_pdf(source)
        
        # Archivo local
        else:
            logger.info(f"Leyendo PDF local: {source}")
            return self._read_local_pdf(source)

    def _download_pdf(self, url: str) -> bytes:
        """Descarga PDF desde URL con validaciones."""
        try:
            with httpx.stream(
                'GET',
                url,
                timeout=self.DOWNLOAD_TIMEOUT,
                follow_redirects=True,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            ) as response:
                if response.status_code != 200:
                    raise ValueError(f"HTTP {response.status_code}")

                # Validar Content-Type
                content_type = response.headers.get('content-type', '').lower()
                if 'pdf' not in content_type:
                    raise ValueError(f"Tipo de contenido inválido: {content_type}")

                # Validar tamaño
                content_length = response.headers.get('content-length')
                if content_length:
                    size = int(content_length)
                    if size > self.MAX_FILE_SIZE:
                        raise ValueError(f"PDF demasiado grande: {size} bytes")

                # Descargar en chunks
                pdf_content = BytesIO()
                downloaded = 0
                
                for chunk in response.iter_bytes(chunk_size=8192):
                    downloaded += len(chunk)
                    if downloaded > self.MAX_FILE_SIZE:
                        raise ValueError("PDF excede tamaño máximo")
                    pdf_content.write(chunk)

                return pdf_content.getvalue()

        except httpx.RequestError as e:
            raise ValueError(f"Error descargando PDF: {e}")

    def _read_local_pdf(self, path: str) -> bytes:
        """Lee PDF local con validaciones de seguridad."""
        
        # Validar ruta
        pdf_path = Path(path).resolve()
        
        # Verificar que está en directorios permitidos
        if not self._is_allowed_path(pdf_path):
            raise ValueError(f"Acceso denegado a: {path}")

        # Validar que existe
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF no encontrado: {path}")

        # Validar que es archivo
        if not pdf_path.is_file():
            raise ValueError(f"No es un archivo: {path}")

        # Validar extensión
        if pdf_path.suffix.lower() != '.pdf':
            raise ValueError(f"Extensión no válida: {pdf_path.suffix}")

        # Validar tamaño
        file_size = pdf_path.stat().st_size
        if file_size > self.MAX_FILE_SIZE:
            raise ValueError(f"PDF demasiado grande: {file_size} bytes")

        # Leer archivo
        try:
            with open(pdf_path, 'rb') as f:
                return f.read()
        except IOError as e:
            raise ValueError(f"Error leyendo PDF: {e}")

    def _is_allowed_path(self, path: Path) -> bool:
        """Verifica que la ruta esté en directorios permitidos."""
        for allowed in self.ALLOWED_PATHS:
            try:
                path.relative_to(Path(allowed).resolve())
                return True
            except ValueError:
                continue
        return False

    def _validate_pdf(self, pdf_content: bytes) -> None:
        """Valida que sea un PDF válido."""
        if not pdf_content.startswith(b'%PDF'):
            raise ValueError("Archivo no es un PDF válido")

        # Intentar parsear
        try:
            reader = PdfReader(BytesIO(pdf_content))
            if len(reader.pages) == 0:
                raise ValueError("PDF no contiene páginas")
            if len(reader.pages) > self.MAX_PAGES:
                raise ValueError(f"PDF tiene demasiadas páginas: {len(reader.pages)}")
        except PdfReadError as e:
            raise ValueError(f"Error parseando PDF: {e}")

    def _parse_pdf(
        self,
        pdf_content: bytes,
        fields: List[str],
        extract_tables: bool,
        search_text: Optional[str],
        use_ocr: bool
    ) -> List[Dict[str, Any]]:
        """Parsea el PDF y extrae datos."""
        
        results = []
        pdf_file = BytesIO(pdf_content)
        reader = PdfReader(pdf_file)

        # Metadatos
        metadata = self._extract_metadata(reader)

        # Procesar cada página
        for page_num, page in enumerate(reader.pages, 1):
            try:
                page_data = self._extract_page_data(
                    page=page,
                    page_num=page_num,
                    fields=fields,
                    extract_tables=extract_tables,
                    search_text=search_text,
                    use_ocr=use_ocr
                )

                if page_data:
                    results.append(page_data)

            except Exception as e:
                logger.warning(f"Error extrayendo página {page_num}: {e}")
                continue

        # Agregar metadatos
        if results and metadata:
            results[0]["_metadata"] = metadata

        return results if results else [{"content": ""}]

    def _extract_metadata(self, reader: PdfReader) -> Dict[str, Any]:
        """Extrae metadatos del PDF."""
        metadata = {}
        
        try:
            if reader.metadata:
                metadata = {
                    "title": reader.metadata.get("/Title"),
                    "author": reader.metadata.get("/Author"),
                    "subject": reader.metadata.get("/Subject"),
                    "pages": len(reader.pages),
                    "is_encrypted": reader.is_encrypted
                }
        except Exception as e:
            logger.debug(f"Error extrayendo metadatos: {e}")

        return metadata

    def _extract_page_data(
        self,
        page,
        page_num: int,
        fields: List[str],
        extract_tables: bool,
        search_text: Optional[str],
        use_ocr: bool
    ) -> Optional[Dict[str, Any]]:
        """Extrae datos de una página."""
        
        page_data = {
            "page": page_num,
            "content": "",
            "tables": [],
            "found": False
        }

        # 1. Extraer texto
        try:
            text = page.extract_text() or ""
            page_data["content"] = text.strip()
        except Exception as e:
            logger.warning(f"Error extrayendo texto página {page_num}: {e}")
            text = ""

        # 2. OCR si es necesario
        if use_ocr and (not text or len(text) < 50):
            logger.debug(f"Aplicando OCR a página {page_num}")
            text = self._apply_ocr(page, page_num)
            page_data["content"] = text

        # 3. Extraer tablas con pdfplumber
        if extract_tables and HAS_PDFPLUMBER:
            tables = self._extract_tables_pdfplumber(BytesIO(page.pdf.stream.read()))
            if tables:
                page_data["tables"] = tables

        # 4. Buscar texto específico
        if search_text:
            if search_text.lower() in text.lower():
                page_data["found"] = True
                # Extraer fragmento
                idx = text.lower().find(search_text.lower())
                start = max(0, idx - 100)
                end = min(len(text), idx + len(search_text) + 100)
                page_data["context"] = text[start:end]

        # 5. Extraer campos específicos
        if fields:
            for field in fields:
                value = self._extract_field_from_text(text, field)
                page_data[field] = value

        return page_data if page_data.get("content") or page_data.get("found") else None

    def _extract_field_from_text(self, text: str, field: str) -> Optional[str]:
        """Busca un campo en el texto usando heurísticas."""
        
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            # Búsqueda simple: "campo: valor"
            if field.lower() in line.lower():
                # Extraer después del campo
                match = re.search(
                    rf'{re.escape(field)}\s*:?\s*([^\n]+)',
                    line,
                    re.IGNORECASE
                )
                if match:
                    return match.group(1).strip()
        
        return None

    def _extract_tables_pdfplumber(self, pdf_file: BytesIO) -> List[Dict[str, Any]]:
        """Extrae tablas usando pdfplumber."""
        if not HAS_PDFPLUMBER:
            return []

        try:
            import pdfplumber
            with pdfplumber.open(pdf_file) as pdf:
                tables = []
                for page in pdf.pages:
                    for table in page.extract_tables():
                        if table:
                            tables.append({
                                "rows": len(table),
                                "columns": len(table[0]) if table else 0,
                                "data": table[:10]  # Primeras 10 filas
                            })
                return tables
        except Exception as e:
            logger.warning(f"Error extrayendo tablas: {e}")
            return []

    def _apply_ocr(self, page, page_num: int) -> str:
        """Aplica OCR usando tesseract."""
        try:
            import pytesseract
            from PIL import Image
            import io

            # Convertir página a imagen
            pix = page.to_image(resolution=150)
            image = Image.open(io.BytesIO(pix))

            # Aplicar OCR
            text = pytesseract.image_to_string(image, lang='spa+eng')
            logger.debug(f"OCR completado para página {page_num}")
            return text

        except ImportError:
            logger.warning("pytesseract o tesseract no instalados")
            return ""
        except Exception as e:
            logger.warning(f"Error en OCR: {e}")
            return ""