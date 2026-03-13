import threading
import asyncio
from concurrent.futures import ThreadPoolExecutor

class ThreadManager:
    def __init__(self, max_workers=5):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.futures = {}
        self.stop_events = {}
        self.browsers_activos = []  # Registro real de browsers para limpieza

    def lanzar(self, nombre, fn, *args, **kwargs):
        """
        Lanza una función en el pool de hilos con un stop_event.
        """
        if nombre in self.futures and not self.futures[nombre].done():
            return False # Ya está corriendo
        
        # Crear evento de parada para este hilo
        event = threading.Event()
        self.stop_events[nombre] = event
        
        # Inyectar stop_event en los argumentos
        kwargs['stop_event'] = event
        
        future = self.executor.submit(fn, *args, **kwargs)
        self.futures[nombre] = future
        return True

    def cancelar(self, nombre):
        """
        Setea el evento de parada para un hilo específico.
        """
        if nombre in self.stop_events:
            self.stop_events[nombre].set()
            # No eliminamos de futures/stop_events aquí, 
            # dejamos que el hilo termine y limpie sus recursos.

    def cancelar_todo(self):
        """
        Setea todos los eventos de parada y cierra browsers registrados.
        """
        for event in self.stop_events.values():
            event.set()
        
        # Intento de cierre de emergencia para browsers registrados
        # Nota: Esto es un fallback si el finally del pipeline falla
        for browser in list(self.browsers_activos):
            try:
                # Si el browser tiene close asíncrono (Playwright)
                if hasattr(browser, 'close'):
                    # Intentamos cerrar de forma segura
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            asyncio.run_coroutine_threadsafe(browser.close(), loop)
                        else:
                            asyncio.run(browser.close())
                    except:
                        pass
            except:
                pass
        
        self.browsers_activos.clear()
        self.futures.clear()
        self.stop_events.clear()

    def registrar_browser(self, browser):
        if browser not in self.browsers_activos:
            self.browsers_activos.append(browser)

    def desregistrar_browser(self, browser):
        if browser in self.browsers_activos:
            self.browsers_activos.remove(browser)
