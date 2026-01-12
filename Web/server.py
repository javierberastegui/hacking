import requests
import time
from dataclasses import dataclass
from typing import Optional, Dict, Any, Callable
from functools import wraps

# --- Configuration & Constants ---
TARGET_URL: str = "https://farmaciatenerife.com"  # Ojo con la URL base
TEST_CALLBACK: str = "audit_security_check_123"
HEADERS: Dict[str, str] = {
    "User-Agent": "Security-Audit-Bot/1.0 (Architecture Check)",
    "Accept": "*/*"
}

# --- Data Structures ---
@dataclass(frozen=True)
class AuditResult:
    """Clase inmutable para encapsular el resultado de la auditoría."""
    is_vulnerable: bool
    status_code: int
    content_type: str
    reflection_found: bool
    message: str

# --- Decorators ---
def latency_tracker(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorador para medir el tiempo de respuesta del servidor."""
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        print(f"⏱️  [Timing] Operación '{func.__name__}' completada en {end_time - start_time:.4f}s")
        return result
    return wrapper

# --- Core Logic ---
class VulnerabilityAuditor:
    """
    Clase encargada de la lógica de negocio para la verificación de CVE-2015-9251.
    Patrón: Fachada para simplificar la complejidad de requests.
    """
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    @latency_tracker
    def check_jsonp_reflection(self, endpoint: str = "/") -> AuditResult:
        """
        Verifica si el servidor refleja el parámetro callback y con qué Content-Type.
        """
        # Construimos la URL de ataque simulado
        target: str = f"{self.base_url}{endpoint}"
        params: Dict[str, str] = {"callback": TEST_CALLBACK}
        
        try:
            print(f"🔍 Auditando: {target} con params={params}")
            response = self.session.get(target, params=params, timeout=10)
            
            # Análisis
            content_type: str = response.headers.get("Content-Type", "").lower()
            body_text: str = response.text
            
            reflection_found: bool = TEST_CALLBACK in body_text
            
            # Lógica de Vulnerabilidad:
            # 1. El callback DEBE estar reflejado en el cuerpo.
            # 2. El Content-Type DEBE ser ejecutable (javascript) para que sea crítico,
            #    AUNQUE si refleja en HTML sigue siendo sucio, pero bloqueado por CORB.
            
            is_risky_mime: bool = "javascript" in content_type or "json" in content_type
            
            if reflection_found and is_risky_mime:
                msg = "CRÍTICO: El servidor devuelve el callback como ejecutable. XSS posible."
                vuln = True
            elif reflection_found and "html" in content_type:
                msg = "ADVERTENCIA: Refleja el input, pero como HTML. El navegador moderno lo bloqueará (CORB), pero es mala práctica."
                vuln = False
            elif not reflection_found:
                msg = "SEGURO: El servidor ignora o sanea el parámetro callback."
                vuln = False
            else:
                msg = "INFO: Comportamiento indeterminado."
                vuln = False

            return AuditResult(
                is_vulnerable=vuln,
                status_code=response.status_code,
                content_type=content_type,
                reflection_found=reflection_found,
                message=msg
            )
            
        except requests.RequestException as e:
            return AuditResult(False, 0, "Error", False, f"Fallo de conexión: {str(e)}")

# --- Execution ---
def main() -> None:
    # Instanciamos el auditor
    auditor = VulnerabilityAuditor(TARGET_URL)
    
    # Ejecutamos la prueba (puedes cambiar el endpoint si sabes dónde está la API)
    # Si la web no tiene API en la raíz, esto dará 404, que es lo normal.
    result: AuditResult = auditor.check_jsonp_reflection()
    
    # Reporte limpio
    print("\n" + "="*50)
    print(f"🛡️  REPORTE DE AUDITORÍA PARA: {TARGET_URL}")
    print("="*50)
    print(f"Estado HTTP   : {result.status_code}")
    print(f"Tipo MIME     : {result.content_type}")
    print(f"Reflejo Input : {'SÍ' if result.reflection_found else 'NO'}")
    print("-" * 50)
    print(f"CONCLUSIÓN    : {result.message}")
    print("="*50)

if __name__ == "__main__":
    main()