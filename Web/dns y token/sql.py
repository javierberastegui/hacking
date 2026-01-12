import subprocess
import os
import sys
from typing import Final, List, Optional, Generator, Any
from dataclasses import dataclass, field
from functools import wraps
from contextlib import contextmanager

# --- Arsenal Avanzado: Decoradores para Lógica Transversal ---

def audit_telemetry(func: Any) -> Any:
    """Decorador para registrar el ciclo de vida de la auditoría."""
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        print(f"\n[bold blue][*][/bold blue] Iniciando secuencia de ataque contra el objetivo...")
        try:
            result = func(*args, **kwargs)
            print(f"[bold green][+][/bold green] Secuencia finalizada con éxito.")
            return result
        except Exception as e:
            print(f"[bold red][!][/bold red] Error crítico en la arquitectura: {e}")
            raise
    return wrapper

# --- Estructura de Datos Estricta ---

@dataclass(frozen=True)
class AuditConfig:
    """Configuración inmutable para la auditoría de seguridad."""
    target_url: str
    risk: int = 3
    level: int = 5
    additional_args: List[str] = field(default_factory=lambda: ["--batch", "--banner", "--random-agent"])

# --- El Corazón del Sistema: Context Managers y Closures ---

class SQLMapEngine:
    """Motor encapsulado para la gestión de subprocesos de SQLMap."""

    def __init__(self, config: AuditConfig):
        self._config: Final[AuditConfig] = config
        self._validate_environment()

    def __repr__(self) -> str:
        return f"<SQLMapEngine(target={self._config.target_url})>"

    def _validate_environment(self) -> None:
        """Dunder-like validation para asegurar que el binario existe."""
        if subprocess.run(["which", "sqlmap"], capture_output=True).returncode != 0:
            raise FileNotFoundError("El binario 'sqlmap' no se encuentra en el PATH. Ejecuta: sudo apt install sqlmap")

    @contextmanager
    def _managed_process(self, command: List[str]) -> Generator[subprocess.Popen, None, None]:
        """Context Manager para asegurar el cierre correcto de los flujos del sistema."""
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        try:
            yield process
        finally:
            process.terminate()
            process.wait()

    @audit_telemetry
    def execute_security_scan(self) -> None:
        """
        Ejecuta el escaneo utilizando un generador para procesar 
        la salida en tiempo real (Scalability pattern).
        """
        base_cmd: List[str] = [
            "sqlmap", "-u", self._config.target_url,
            "--risk", str(self._config.risk),
            "--level", str(self._config.level)
        ] + self._config.additional_args

        with self._managed_process(base_cmd) as process:
            # Uso de generador para evitar bloqueos de memoria en logs masivos
            if process.stdout:
                for line in iter(process.stdout.readline, ""):
                    print(f"  > {line.strip()}")

# --- Factory Pattern con Closures para Interactividad ---

def audit_factory() -> None:
    """Punto de entrada interactivo que encapsula la instanciación."""
    print("=== SQL INJECTION AUDIT SUITE (SENIOR EDITION) ===")
    
    # Aquí es donde el programa te pregunta la URL, como pediste
    url: str = input("\n[?] Introduce la URL del objetivo (ej. http://tusiite.com/page.php?id=1): ").strip()
    
    if not url:
        print("[-] La URL no puede estar vacía, colega.")
        return

    # Inyectamos la configuración en el motor
    config = AuditConfig(target_url=url)
    engine = SQLMapEngine(config)
    
    engine.execute_security_scan()

if __name__ == "__main__":
    try:
        audit_factory()
    except KeyboardInterrupt:
        print("\n[!] Auditoría abortada por el usuario. Saliendo de forma limpia...")
        sys.exit(0)