import time
import asyncio
from functools import wraps

class RateLimiter:
    """
    Rate Limiter: Control request frequency.
    """
    def __init__(self, requests_per_second=1):
        self.delay = 1.0 / requests_per_second
        self.last_request = 0
        self.lock = threading.Lock() if 'threading' in globals() else None

    def wait(self):
        """Synchronous wait"""
        now = time.time()
        wait_time = self.delay - (now - self.last_request)
        if wait_time > 0:
            time.sleep(wait_time)
        self.last_request = time.time()

    async def wait_async(self):
        """Asynchronous wait"""
        now = asyncio.get_event_loop().time()
        wait_time = self.delay - (now - self.last_request)
        if wait_time > 0:
            await asyncio.sleep(wait_time)
        self.last_request = asyncio.get_event_loop().time()

def con_reintentos(max_retries=3, delay=2):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            for intento in range(max_retries):
                try:
                    return fn(*args, **kwargs)
                except Exception as e:
                    if intento == max_retries - 1:
                        raise e
                    time.sleep(delay * (intento + 1))
            return None
        return wrapper
    return decorator

def con_reintentos_async(max_retries=3, delay=2):
    def decorator(fn):
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            import asyncio
            for intento in range(max_retries):
                try:
                    return await fn(*args, **kwargs)
                except Exception as e:
                    if intento == max_retries - 1:
                        raise e
                    await asyncio.sleep(delay * (intento + 1))
            return None
        return wrapper
    return decorator
