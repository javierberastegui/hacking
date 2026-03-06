import subprocess
from dataclasses import dataclass
from typing import List, Optional, Callable
from enum import Enum

class DNSServer(Enum):
    GOOGLE = "8.8.8.8"
    CLOUDFLARE = "1.1.1.1"

@dataclass(frozen=True)
class DNSResult:
    """Contenedor inmutable para los resultados de la consulta."""
    domain: str
    server: str
    records: List[str]
    is_valid: bool

class DNSInspector:
    """
    Clase encargada de la lógica de inspección de DNS.
    Usa el patrón de inyección para los servidores si quisiéramos escalar.
    """
    
    def __init__(self, timeout: int = 5):
        self._timeout = timeout

    def _execute_dig(self, domain: str, server: str) -> List[str]:
        """Encapsula la ejecución del comando dig."""
        command: List[str] = ["dig", f"@{server}", "NS", domain, "+short"]
        
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=self._timeout,
                check=True
            )
            return [line.strip() for line in result.stdout.splitlines() if line.strip()]
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return []

    def audit_domain(self, domain: str) -> List[DNSResult]:
        """
        Realiza la auditoría en múltiples servidores. 
        Ideal para detectar inconsistencias de propagación.
        """
        results: List[DNSResult] = []
        
        for server in DNSServer:
            records = self._execute_dig(domain, server.value)
            results.append(DNSResult(
                domain=domain,
                server=server.name,
                records=records,
                is_valid=len(records) > 0
            ))
        
        return results

# --- Decorador para loguear la actividad (Lógica Transversal) ---
def log_audit(func: Callable) -> Callable:
    def wrapper(*args, **kwargs):
        print(f"🚀 Iniciando auditoría para: {args[1] if len(args) > 1 else 'Desconocido'}")
        result = func(*args, **kwargs)
        print("✅ Auditoría completada.")
        return result
    return wrapper

@log_audit
def run_plugin(inspector: DNSInspector, domain: str) -> None:
    results = inspector.audit_domain(domain)
    
    for res in results:
        status = "🟢" if res.is_valid else "🔴"
        print(f"{status} [{res.server}] Records para {res.domain}: {', '.join(res.records) or 'Ninguno'}")

# --- Entry Point ---
if __name__ == "__main__":
    # Mock de input de usuario
    user_input = input("Introduce el dominio (ej. farmaciapuentezurita.com): ").strip()
    
    if user_input:
        dns_tool = DNSInspector()
        run_plugin(dns_tool, user_input)
    else:
        print("¿En serio me vas a pasar un string vacío? Sube el nivel, Lokky.")