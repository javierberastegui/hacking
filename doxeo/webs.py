import asyncio
import aiohttp
import time
from dataclasses import dataclass
from typing import List, Optional, Callable
from functools import wraps

# --- Domain Logic ---

@dataclass(frozen=True)
class CheckResult:
    url: str
    status: int
    is_active: bool
    server: Optional[str] = "N/A"

# --- Decorators for Cross-Cutting Concerns ---

def execution_timer(func: Callable):
    """Mide el tiempo de ejecución para optimizar el tuning de concurrencia."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = await func(*args, **kwargs)
        end = time.perf_counter()
        print(f"\n[!] Scan completado en {end - start:.2f} segundos.")
        return result
    return wrapper

# --- The Architect's Core ---

class URLScanner:
    def __init__(self, concurrency_limit: int = 50, timeout: int = 10):
        self.semaphore = asyncio.Semaphore(concurrency_limit)
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Asset-Discovery-Tool/1.0"
        }

    async def _check_status(self, session: aiohttp.ClientSession, url: str) -> CheckResult:
        """Realiza la petición atómica con gestión de errores profesional."""
        # Aseguramos el esquema, subfinder solo suelta el dominio
        target_url = url if url.startswith(("http://", "https://")) else f"https://{url}"
        
        async with self.semaphore:
            try:
                async with session.get(target_url, timeout=self.timeout, ssl=False) as response:
                    return CheckResult(
                        url=target_url,
                        status=response.status,
                        is_active=200 <= response.status < 400,
                        server=response.headers.get("Server")
                    )
            except Exception:
                # Si falla HTTPS, un Senior intentaría HTTP, pero aquí lo marcamos como caído
                return CheckResult(url=target_url, status=0, is_active=False)

    @execution_timer
    async def run_scan(self, domains: List[str]) -> List[CheckResult]:
        """Orquestador de la ejecución masiva."""
        async with aiohttp.ClientSession(headers=self.headers) as session:
            tasks = [self._check_status(session, domain.strip()) for domain in domains]
            return await asyncio.gather(*tasks)

# --- Entry Point ---

async def main():
    # Asumimos que el archivo se llama 'subdomains.txt'
    try:
        with open("subdomains.txt", "r") as f:
            domains = f.readlines()
    except FileNotFoundError:
        print("[-] Error: 'subdomains.txt' no encontrado. Pásale el output de subfinder.")
        return

    scanner = URLScanner(concurrency_limit=100) # Sube esto si tu conexión es de la NASA
    results = await scanner.run_scan(domains)

    # Presentación de resultados filtrando solo los 'vivos'
    print(f"{'URL':<60} | {'STATUS':<8} | {'SERVER'}")
    print("-" * 85)
    
    active_count = 0
    for res in results:
        if res.is_active:
            print(f"{res.url:<60} | {res.status:<8} | {res.server}")
            active_count += 1
            
    print(f"\n[+] Se encontraron {active_count} URLs activas de {len(domains)} analizadas.")

if __name__ == "__main__":
    asyncio.run(main())