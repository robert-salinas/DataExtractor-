import threading
from collections import deque

class ProxyManager:
    def __init__(self, proxies: list = None):
        self.pool = deque(proxies) if proxies else deque()
        self.baneados = set()
        self.lock = threading.Lock()
    
    def obtener(self):
        with self.lock:
            for _ in range(len(self.pool)):
                proxy = self.pool[0]
                self.pool.rotate(-1)
                if proxy not in self.baneados:
                    return proxy
            return None  # todos baneados 
    
    def reportar_baneo(self, proxy):
        with self.lock:
            self.baneados.add(proxy)
            print(f"[PROXY] Baneado: {proxy}")
    
    def cargar_desde_archivo(self, path):
        try:
            with open(path) as f:
                new_proxies = [line.strip() for line in f if line.strip()]
                with self.lock:
                    self.pool = deque(new_proxies)
                    self.baneados.clear()
            return True
        except Exception as e:
            print(f"[ERROR] No se pudo cargar proxies: {e}")
            return False
