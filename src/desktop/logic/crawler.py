import asyncio
from typing import Set, Dict, Any, List

class CrawlerRecursivo:
    def __init__(self, max_depth=3, max_pages=50):
        self.visitados: Set[str] = set()
        self.cola = asyncio.Queue()
        self.max_depth = max_depth
        self.max_pages = max_pages
    
    async def crawl(self, url_inicial: str, pipeline_fn):
        """
        Recursive Crawler: BFS traversal with depth control.
        """
        await self.cola.put((url_inicial, 0))
        
        while not self.cola.empty():
            if len(self.visitados) >= self.max_pages:
                break
                
            url, depth = await self.cola.get()
            
            if url in self.visitados or depth > self.max_depth:
                continue 
            
            self.visitados.add(url)
            
            # Extrae datos y links nuevos 
            # pipeline_fn should be async or we wrap it
            try:
                # Assuming pipeline_fn is synchronous for now as we use playwright sync_api
                # We'll use loop.run_in_executor if needed or make it async
                # For simplicity, we'll call it directly if it's sync
                resultado = await asyncio.to_thread(pipeline_fn, url)
                
                # yield url and result for extraction logic
                yield url, resultado
                
                # Add new links to queue
                for link in resultado.get("links", []):
                    if link not in self.visitados:
                        await self.cola.put((link, depth + 1))
            except Exception as e:
                print(f"[CRAWLER] Error en {url}: {e}")
                continue
