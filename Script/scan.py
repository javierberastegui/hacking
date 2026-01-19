import asyncio
import aiohttp
from typing import Callable, Any, Optional, Dict, List
from dataclasses import dataclass, field
from functools import wraps

@dataclass(frozen=True)
class SiteCheckResult:
    site_name: str
    exists: bool
    status_code: int = 0
    error: Optional[str] = None

def with_resilience(retries: int = 2):
    """
    Decorador avanzado para gestionar reintentos y timeouts.
    Si el sitio se pone tonto, lo reintentamos antes de darlo por muerto.
    """
    def decorator(func: Callable[..., Any]):
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_err = None
            for attempt in range(retries):
                try:
                    # Timeout total por cada petición individual
                    return await asyncio.wait_for(func(*args, **kwargs), timeout=5.0)
                except Exception as e:
                    last_err = e
            # Si llegamos aquí, es que ha fallado todos los intentos
            return SiteCheckResult(args[1], False, 0, f"Timeout/Error: {last_err}")
        return wrapper
    return decorator

class SherlockEngine:
    """
    Motor asíncrono de alto rendimiento. 
    Implementa el protocolo de Context Manager para gestión de recursos.
    """
    def __init__(self, max_concurrent: int = 15):
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._session: Optional[aiohttp.ClientSession] = None
        self._headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        }

    async def __aenter__(self):
        # Inicializamos la sesión de forma perezosa (lazy loading)
        self._session = aiohttp.ClientSession(headers=self._headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()

    @with_resilience(retries=2)
    async def check_site(self, url_template: str, site_name: str, username: str) -> SiteCheckResult:
        """Realiza la comprobación real mediante una petición HEAD (más ligera)."""
        if not self._session:
            raise RuntimeError("Sesión no inicializada. Usa el context manager 'async with'.")

        url = url_template.format(username)
        
        async with self._semaphore:
            try:
                # Usamos HEAD para no descargar todo el HTML, solo queremos ver si existe
                async with self._session.head(url, allow_redirects=True, timeout=5) as response:
                    # Lógica simple: si es 200, el usuario existe. 
                    # Algunos sitios devuelven 404, otros te redirigen (ojo ahí).
                    exists = response.status == 200
                    return SiteCheckResult(site_name, exists, response.status)
            except Exception as e:
                return SiteCheckResult(site_name, False, 0, str(e))

async def main():
    # Definición de objetivos (Esto debería venir de un JSON en un sistema real)
    targets = {
        "GitHub": "https://github.com/{}",
        "Twitter": "https://twitter.com/{}",
        "Instagram": "https://www.instagram.com/{}/",
        "Reddit": "https://www.reddit.com/user/{}/",
    }
    
    username = "rocsifs"

    # Uso del motor con gestión automática de recursos
    async with SherlockEngine(max_concurrent=5) as engine:
        print(f"[*] Escaneando rastro de '{username}' en la red...\n")
        
        tasks = [engine.check_site(url, name, username) for name, url in targets.items()]
        results = await asyncio.gather(*tasks)

        for res in results:
            icon = "✅ FOUND" if res.exists else "❌ NOT FOUND"
            meta = f"[HTTP {res.status_code}]" if res.status_code else f"[ERR: {res.error}]"
            print(f"{icon:<12} | {res.site_name:<12} {meta}")

if __name__ == "__main__":
    asyncio.run(main())