import re
import os
import pandas as pd
from typing import List, Dict, Any, Optional
from pathlib import Path

# Modular imports
from src.desktop.logic.config_manager import ConfigManager
from src.desktop.logic.detector import PATTERNS, detectar_input
from src.desktop.logic.thread_manager import ThreadManager
from src.desktop.logic.db import DatabaseManager
from src.desktop.logic.deobfuscator import decodificar
from src.desktop.logic.proxy_manager import ProxyManager
from src.desktop.logic.validator import es_dato_valido
from src.desktop.logic.exporter import Exporter
from src.desktop.logic.crawler import CrawlerRecursivo
from src.desktop.logic.pipelines.web import pipeline_web
from src.desktop.logic.osint import OSINTPipeline
from src.desktop.logic.sqli import SQLiProbe
from src.desktop.logic.retry import RateLimiter

class ExtractionLogic:
    """
    Main Engine: Orchestrates modular components for RS Omni-Extractor.
    """
    def __init__(self):
        self.results: List[str] = []
        self.current_data_type: str = "Unknown"
        self.file_size: str = "0 KB"
        
        # Modules
        self.config = ConfigManager()
        self.db = DatabaseManager()
        self.thread_manager = ThreadManager(max_workers=5)
        self.proxy_manager = ProxyManager()
        self.exporter = Exporter()
        self.osint = OSINTPipeline()
        self.sqli = SQLiProbe()
        self.rate_limiter = RateLimiter(requests_per_second=2)
        self.PATTERNS = PATTERNS

    def detectar_input(self, data: str) -> str:
        return detectar_input(data)

    async def run_sqli_pipeline(self, target: str) -> List[Dict[str, Any]]:
        """
        SQLi Pipeline Execution.
        """
        proxy = self.proxy_manager.obtener()
        self.sqli.proxies = {"http": proxy, "https": proxy} if proxy else None
        
        results = []
        if "?" in target:
            # Extract parameters
            query = target.split("?", 1)[1]
            params = [p.split("=")[0] for p in query.split("&") if "=" in p]
            for param in params:
                res = await self.sqli.probe(target, param)
                results.extend(res)
        return results

    async def run_osint_pipeline(self, target: str) -> List[Dict[str, Any]]:
        """
        OSINT Pipeline Execution.
        """
        proxy = self.proxy_manager.obtener()
        self.osint.proxy = {"http": proxy, "https": proxy} if proxy else None
        
        # Apply Rate Limiting
        await self.rate_limiter.wait_async()
        
        try:
            results = await self.osint.run_full_pipeline(target)
            return results
        except Exception as e:
            if proxy:
                self.proxy_manager.reportar_baneo(proxy)
            raise e

    def scrape_with_playwright(self, url: str) -> Dict[str, Any]:
        """
        Scrape a single URL with proxy support, rate limiting and stop event support.
        """
        import time
        self.rate_limiter.wait() # Sync wait
        
        proxy = self.proxy_manager.obtener()
        try:
            # Obtener el stop_event si existe en el contexto del hilo actual
            # (Aunque aquí lo pasaremos si se llama desde un hilo gestionado)
            result = pipeline_web(url, proxy=proxy, thread_manager=self.thread_manager)
            return result
        except Exception as e:
            if proxy:
                self.proxy_manager.reportar_baneo(proxy)
            raise e

    def extract_from_text(self, text: str, pattern_name: str = "Auto", custom_regex: str = "") -> List[str]:
        """
        Core Extraction Engine with Deobfuscation and Validation.
        """
        try:
            # 1. Deobfuscation
            decoded_texts = decodificar(text)
            full_text = text + "\n" + "\n".join(decoded_texts)
            
            # 2. Regex Extraction
            matches = []
            if custom_regex:
                matches = re.findall(custom_regex, full_text, re.IGNORECASE | re.MULTILINE)
            elif pattern_name == "Auto":
                for name, p in self.PATTERNS.items():
                    if name != "HTML":
                        found = re.findall(p, full_text, re.IGNORECASE | re.MULTILINE)
                        matches.extend(found)
            elif pattern_name in self.PATTERNS:
                matches = re.findall(self.PATTERNS[pattern_name], full_text, re.IGNORECASE | re.MULTILINE)

            # 3. Clean, Validate and Unique
            final_results = []
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                
                match = match.strip()
                if es_dato_valido(match, pattern_name):
                    final_results.append(match)
            
            self.results = sorted(list(set(final_results)))
            return self.results
        except Exception as e:
            print(f"[ERROR] Extracción falló: {str(e)}")
            return []

    def save_to_sqlite(self, data_type: str, results: List[str], target_input: str = ""):
        """Persist to SQLite using DatabaseManager"""
        return self.db.save_results(data_type, results, target_input)

    def load_file(self, file_path: str) -> str:
        """
        Load text content from supported file types.
        """
        path = Path(file_path)
        if not path.exists():
            return "Error: File not found"
        
        # Calculate file size
        size_bytes = path.stat().st_size
        self.file_size = f"{size_bytes / 1024:.1f} KB" if size_bytes < 1024 * 1024 else f"{size_bytes / (1024 * 1024):.1f} MB"
        
        # Supported extensions
        ext = path.suffix.lower()
        if ext == '.txt':
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        elif ext == '.csv':
            df = pd.read_csv(path)
            return df.to_string()
        elif ext == '.xlsx':
            df = pd.read_excel(path)
            return df.to_string()
        elif ext == '.pdf':
            import PyPDF2
            text = ""
            with open(path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text()
            return text
        else:
            return "Error: Unsupported file format"
