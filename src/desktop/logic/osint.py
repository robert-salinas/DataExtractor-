import asyncio
import dns.resolver
import requests
import aiohttp
from typing import List, Dict, Any
from src.desktop.logic.config_manager import ConfigManager

class OSINTPipeline:
    """
    OSINT Pipeline: DNS, Subdomains, Tech Detection, and Exposure.
    """
    def __init__(self, proxy=None):
        self.config = ConfigManager()
        self.proxy = {"http": proxy, "https": proxy} if proxy else None
        self.proxy_str = proxy
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

    async def breach_check(self, email: str) -> List[Dict[str, str]]:
        """Check for email breaches via LeakCheck.io public API."""
        if not self.config.get('osint', 'breach_check', True):
            return []
            
        results = []
        url = f"https://leakcheck.io/api/public?check={email}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, proxy=self.proxy_str, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("found", False):
                            results.append({
                                "tipo": "BREACH_FOUND", 
                                "valor": f"{email} | Fuentes: {', '.join(data.get('sources', []))}"
                            })
                    else:
                        print(f"[OSINT ERROR] LeakCheck API respondió con status {response.status}")
        except Exception as e:
            print(f"[OSINT ERROR] Falló Breach Check para {email}: {e}")
        return results

    async def dns_enum(self, domain: str) -> List[Dict[str, str]]:
        """Full DNS enumeration based on config."""
        results = []
        record_types = self.config.get('osint', 'dns_tipos', ['A', 'MX', 'TXT', 'NS', 'SOA', 'AAAA'])
        
        resolver = dns.resolver.Resolver()
        resolver.timeout = 2
        resolver.lifetime = 2
        
        for record_type in record_types:
            try:
                # Especial handling for DMARC/SPF which are usually TXT
                target = domain
                if record_type == "DMARC":
                    target = f"_dmarc.{domain}"
                    record_type = "TXT"
                
                answers = await asyncio.to_thread(resolver.resolve, target, record_type)
                for rdata in answers:
                    val = str(rdata)
                    # Detect SPF within TXT
                    if record_type == "TXT" and "v=spf1" in val:
                        results.append({"tipo": "SPF", "valor": val})
                    else:
                        results.append({"tipo": f"DNS_{record_type}", "valor": val})
            except Exception as e:
                # Silent skip for missing records, log others
                if not isinstance(e, (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers)):
                    print(f"[OSINT ERROR] DNS Enum ({record_type}) para {domain}: {e}")
                continue
        
        return results

    async def subdomain_enum(self, domain: str) -> List[Dict[str, str]]:
        """Crt.sh subdomain enumeration with wildcard filtering."""
        results = []
        max_limit = self.config.get('osint', 'max_subdominios', 100)
        url = f"https://crt.sh/?q=%25.{domain}&output=json"
        
        try:
            response = await asyncio.to_thread(requests.get, url, headers=self.headers, proxies=self.proxy, timeout=15)
            if response.status_code == 200:
                data = response.json()
                subdomains = set()
                for entry in data:
                    name = entry['name_value'].lower()
                    # Filter wildcards and split multiple names
                    for n in name.split("\n"):
                        n = n.strip()
                        if n.startswith("*."): continue # Ignore wildcard results
                        if n.endswith(domain) and n != domain:
                            subdomains.add(n)
                            if len(subdomains) >= max_limit: break
                    if len(subdomains) >= max_limit: break
                
                for sub in subdomains:
                    results.append({"tipo": "SUBDOMAIN", "valor": sub})
            else:
                print(f"[OSINT ERROR] Crt.sh respondió con status {response.status_code}")
        except Exception as e:
            print(f"[OSINT ERROR] Subdomain Enum para {domain}: {e}")
            
        return results

    async def tech_detect(self, url: str) -> List[Dict[str, str]]:
        """Basic Technology Detection via Headers and HTML."""
        results = []
        if not url.startswith('http'):
            url = f"https://{url}"
            
        try:
            response = await asyncio.to_thread(requests.get, url, headers=self.headers, proxies=self.proxy, timeout=10, verify=False)
            
            # Headers
            for header, label in [("Server", "TECH_SERVER"), ("X-Powered-By", "TECH_PLATFORM")]:
                val = response.headers.get(header)
                if val: results.append({"tipo": label, "valor": val})

            # HTML Analysis
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            meta_generator = soup.find("meta", attrs={"name": "generator"})
            if meta_generator:
                results.append({"tipo": "TECH_GENERATOR", "valor": meta_generator.get("content")})
            
            # Detect CMS
            cms_patterns = [("wp-content", "WordPress"), ("Drupal", "Drupal"), ("Joomla", "Joomla")]
            for pattern, name in cms_patterns:
                if pattern in response.text:
                    results.append({"tipo": "TECH_CMS", "valor": name})
                
        except Exception as e:
            print(f"[OSINT ERROR] Tech Detect para {url}: {e}")
            
        return results

    async def run_full_pipeline(self, target: str) -> List[Dict[str, str]]:
        """Orchestrate all OSINT tasks."""
        domain = target.replace("https://", "").replace("http://", "").split("/")[0]
        
        tasks = [
            self.dns_enum(domain),
            self.subdomain_enum(domain),
            self.tech_detect(target if target.startswith("http") else domain)
        ]
        
        if "@" in target:
            tasks.append(self.breach_check(target))

        all_results = await asyncio.gather(*tasks)
        return [item for sublist in all_results for item in sublist]
