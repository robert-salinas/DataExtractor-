from playwright_stealth import stealth
from fake_useragent import UserAgent

ua = UserAgent()

def browser_stealth(page):
    """
    Apply real stealth settings to playwright page.
    """
    stealth(page)
    return page

def get_random_ua():
    return ua.random

async def launch_stealth_browser(playwright_instance):
    """
    Launch browser with advanced evasion (non-headless + args).
    """
    args = [
        "--window-position=-32000,-32000", # Minimizar fuera de pantalla
        "--disable-blink-features=AutomationControlled",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-web-security",
        "--disable-features=IsolateOrigins,site-per-process"
    ]
    
    try:
        # Intento 1: No-headless real
        browser = await playwright_instance.chromium.launch(
            headless=False,
            args=args
        )
        return browser
    except Exception as e:
        # Fallback 1: Headless con canal Chrome real (mejor TLS)
        try:
            browser = await playwright_instance.chromium.launch(
                headless=True,
                channel="chrome",
                args=args
            )
            return browser
        except:
            # Fallback 2: Headless estándar
            return await playwright_instance.chromium.launch(
                headless=True,
                args=args
            )
