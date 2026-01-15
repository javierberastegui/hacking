import asyncio
import httpx
from typing import Final, Callable, Any, Optional, Protocol
from dataclasses import dataclass
from functools import wraps

# --- ESTRUCTURAS DE DATOS ---
@dataclass(frozen=True)
class CVEImpact:
    id: str
    description: str
    severity: str
    base_score: float

# --- PROTOCOLO PARA INVERSIÓN DE DEPENDENCIAS ---
class VulnProvider(Protocol):
    async def fetch_cve(self, cve_id: str) -> Optional[CVEImpact]:
        ...

# --- DECORADOR PARA RESILIENCIA ---
def retry_on_failure(retries: int = 3):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for i in range(retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if i == retries - 1: raise e
                    print(f"[!] Error detectado. Reintento {i+1}/{retries}...")
                    await asyncio.sleep(1)
        return wrapper
    return decorator

# --- CLOSURE PARA GESTIÓN DE CLIENTE API ---
def nvd_api_factory(base_url: str = "https://services.nvd.nist.gov/rest/json/cves/2.0"):
    """Encapsula la configuración de la API y el cliente."""
    _headers: Final = {"User-Agent": "Sentinel-Scanner-Pro"}

    async def get_cve_data(cve_id: str) -> Optional[CVEImpact]:
        async with httpx.AsyncClient(timeout=10.0, headers=_headers) as client:
            params = {"cveId": cve_id}
            response = await client.get(base_url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                # Lógica de parsing (simplificada para el ejemplo)
                vulnerabilities = data.get("vulnerabilities", [])
                if not vulnerabilities: return None
                
                cve_info = vulnerabilities[0]["cve"]
                return CVEImpact(
                    id=cve_id,
                    description=cve_info["descriptions"][0]["value"],
                    severity="HIGH", # Esto vendría del JSON real
                    base_score=9.8
                )
            return None
    
    return get_cve_data

# --- CLASE PRINCIPAL (ORQUESTADOR) ---
class VulnerabilitySentinel:
    def __init__(self, fetcher: Callable):
        self._fetcher = fetcher

    @retry_on_failure(retries=2)
    async def audit_cve(self, cve_id: str) -> None:
        """Auditoría asíncrona con reporte inmediato."""
        print(f"[*] Consultando inteligencia para {cve_id}...")
        impact = await self._fetcher(cve_id)
        
        if impact:
            print(f"\n[!!!] ALERTA DE VULNERABILIDAD [!!!]")
            print(f"ID: {impact.id} | Score: {impact.base_score}")
            print(f"Resumen: {impact.description[:100]}...\n")
        else:
            print(f"[-] No se encontró información crítica para {cve_id}.")

    def __str__(self) -> str:
        return f"<Sentinel Engine v2.0 Active>"

# --- ENTRY POINT ---
async def main():
    # Instanciamos mediante el closure
    nvd_fetcher = nvd_api_factory()
    sentinel = VulnerabilitySentinel(nvd_fetcher)
    
    # Podrías lanzar varios en paralelo con asyncio.gather
    await sentinel.audit_cve("CVE-2025-58674")

if __name__ == "__main__":
    asyncio.run(main())