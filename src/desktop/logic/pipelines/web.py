import time
import asyncio
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from src.desktop.logic.stealth import browser_stealth, get_random_ua, launch_stealth_browser
from src.desktop.logic.proxy_manager import ProxyManager

# Códigos de error para manejo de reintentos
RETRY_CODES = {429, 503, 502, 520, 521, 522}
NO_RETRY_CODES = {404, 403, 401, 400}

class RetryableError(Exception): pass
class NoRetryError(Exception): pass

def pipeline_web(url: str, proxy: str = None, stop_event=None, thread_manager=None) -> dict:
    """
    Pipeline Web: Real Stealth scraping with Playwright + Contextual Proxy + Stop Event.
    """
    # Usar loop asíncrono para Playwright moderno
    return asyncio.run(_pipeline_web_async(url, proxy, stop_event, thread_manager))

async def _pipeline_web_async(url: str, proxy: str = None, stop_event=None, thread_manager=None) -> dict:
    from playwright.async_api import async_playwright
    
    max_retries = 3
    current_retry = 0
    
    # Manejador de proxies local si no se provee uno
    pm = ProxyManager()
    
    async with async_playwright() as p:
        # 1. Launch Browser (Advanced Evasion)
        browser = await launch_stealth_browser(p)
        
        # Registrar browser para cierre de emergencia si hay thread_manager
        if thread_manager:
            thread_manager.registrar_browser(browser)
            
        try:
            while current_retry < max_retries:
                # Chequeo de parada
                if stop_event and stop_event.is_set():
                    return {"text": "", "links": [], "status": "cancelled"}

                # 2. Proxy Rotation per Context
                current_proxy = proxy or pm.obtener()
                context_args = {
                    "user_agent": get_random_ua(),
                    "viewport": {"width": 1366, "height": 768},
                    "locale": "es-PY",
                    "timezone_id": "America/Asuncion"
                }
                if current_proxy:
                    context_args["proxy"] = {"server": current_proxy}
                
                context = await browser.new_context(**context_args)
                page = await context.new_page()
                await browser_stealth(page)
                
                try:
                    print(f"[PIPELINE] Accediendo a {url} (Intento {current_retry+1}, Proxy: {current_proxy})...")
                    
                    # 3. Request con lógica de reintentos e interrupción
                    response = await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                    
                    # --- Cloudflare Detection & Bypass Logic ---
                    content = await page.content()
                    is_cf = any(term in content for term in ["Cloudflare", "Checking your browser", "DDoS protection"]) or \
                            "cf-ray" in (response.headers if response else {})

                    if is_cf:
                        print(f"[STEALTH] Cloudflare detectado en {url}. Activando modo evasión...")
                        # Emulación de movimiento de mouse humano
                        await page.mouse.move(100, 100)
                        await page.mouse.move(200, 300, steps=10)
                        await page.mouse.move(400, 200, steps=10)
                        
                        # Esperar resolución de reto (JS challenge o Turnstile)
                        # Buscamos que el título cambie o que aparezca contenido real
                        try:
                            await page.wait_for_selector("text=Checking your browser", state="hidden", timeout=20000)
                            await page.wait_for_load_state("networkidle", timeout=10000)
                            # Re-evaluamos response si cambió la página
                            response = await page.request.get(url) if response.status != 200 else response
                        except:
                            print("[WARN] Tiempo de espera de Cloudflare excedido.")

                    if not response:
                        raise RetryableError("No response from server")
                        
                    if response.status in NO_RETRY_CODES:
                        raise NoRetryError(f"HTTP {response.status}")
                        
                    if response.status in RETRY_CODES:
                        raise RetryableError(f"HTTP {response.status}")

                    # 4. Success - Parse Content
                    # Stealth Scroll
                    if stop_event and not stop_event.is_set():
                        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        await asyncio.sleep(1)
                    
                    content = await page.content()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    for s in soup(["script", "style", "nav", "footer", "header"]):
                        s.decompose()
                    
                    elements = [tag.get_text().strip() for tag in soup.find_all(['h1', 'h2', 'h3', 'p', 'a']) if tag.get_text().strip()]
                    
                    links = []
                    for a in soup.find_all('a', href=True):
                        href = a['href']
                        if href.startswith('http'):
                            links.append(href)
                        elif href.startswith('/'):
                            from urllib.parse import urljoin
                            links.append(urljoin(url, href))
                    
                    return {
                        "text": '\n'.join(elements),
                        "links": list(set(links)),
                        "status": "success"
                    }

                except NoRetryError as e:
                    print(f"[ERROR] Error fatal (sin reintento): {str(e)}")
                    return {"text": "", "links": [], "status": "error", "error": str(e)}
                    
                except (RetryableError, Exception) as e:
                    current_retry += 1
                    print(f"[RETRY] Fallo temporal ({current_retry}/{max_retries}): {str(e)}")
                    if current_proxy and pm:
                        pm.reportar_baneo(current_proxy)
                    
                    if current_retry < max_retries:
                        # Espera asíncrona con chequeo de parada
                        for _ in range(int(2 * current_retry)):
                            if stop_event and stop_event.is_set(): break
                            await asyncio.sleep(1)
                finally:
                    await context.close()

            return {"text": "", "links": [], "status": "failed_after_retries"}

        finally:
            # 5. Cleanup Browser
            await browser.close()
            if thread_manager:
                thread_manager.desregistrar_browser(browser)
