import requests
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum
import sys

# --- Configuration ---
TARGET_URL = "https://farmaciatenerife.com" # Cambia esto si pruebas en local

class SecurityLevel(Enum):
    OK = "✅ PASS"
    WARNING = "⚠️ WARN"
    CRITICAL = "❌ FAIL"

@dataclass
class HeaderCheck:
    header_name: str
    description: str
    severity: str  # 'High', 'Medium', 'Low'
    expected_value: Optional[str] = None
    status: SecurityLevel = SecurityLevel.CRITICAL
    found_value: Optional[str] = None

@dataclass
class SecurityReport:
    target: str
    score: int = 100
    checks: List[HeaderCheck] = field(default_factory=list)

    def deduct_score(self, points: int):
        self.score = max(0, self.score - points)

class EnterpriseAuditor:
    """
    Auditor de seguridad enfocado en cabeceras HTTP de defensa moderna.
    Implementa un patrón de estrategia simple para validar reglas.
    """
    
    def __init__(self, url: str):
        self.url = url
        self.report = SecurityReport(target=url)
        self.headers: Dict[str, str] = {}

    def _fetch_headers(self) -> bool:
        try:
            # User-Agent profesional para no ser bloqueado por WAFs básicos
            ua = "Mozilla/5.0 (Compatible; EnterpriseSecAudit/2.1; +internal_audit)"
            response = requests.head(self.url, headers={"User-Agent": ua}, timeout=5)
            self.headers = {k.lower(): v for k, v in response.headers.items()}
            return True
        except requests.RequestException as e:
            print(f"[!] Error fatal conectando al target: {e}")
            return False

    def _check_hsts(self):
        """Strict-Transport-Security: Fuerza HTTPS."""
        check = HeaderCheck("Strict-Transport-Security", "Previene ataques MITM forzando HTTPS", "High")
        val = self.headers.get("strict-transport-security")
        
        if val:
            check.status = SecurityLevel.OK
            check.found_value = val[:20] + "..."
        else:
            check.status = SecurityLevel.CRITICAL
            check.found_value = "MISSING"
            self.report.deduct_score(20)
        
        self.report.checks.append(check)

    def _check_csp(self):
        """Content-Security-Policy: Mitigación de XSS."""
        check = HeaderCheck("Content-Security-Policy", "Lista blanca de recursos ejecutables (XSS Shield)", "High")
        val = self.headers.get("content-security-policy")
        
        if val:
            if "unsafe-inline" in val or "unsafe-eval" in val:
                check.status = SecurityLevel.WARNING
                check.found_value = "WEAK POLICY"
                self.report.deduct_score(10)
            else:
                check.status = SecurityLevel.OK
                check.found_value = "Present"
        else:
            check.status = SecurityLevel.CRITICAL
            check.found_value = "MISSING"
            self.report.deduct_score(25)
        
        self.report.checks.append(check)

    def _check_clickjacking(self):
        """X-Frame-Options: Previene UI Redressing."""
        check = HeaderCheck("X-Frame-Options", "Evita que la web se cargue en iFrames (Clickjacking)", "Medium")
        val = self.headers.get("x-frame-options")
        
        if val and val.upper() in ["DENY", "SAMEORIGIN"]:
            check.status = SecurityLevel.OK
            check.found_value = val
        else:
            check.status = SecurityLevel.CRITICAL
            check.found_value = "MISSING"
            self.report.deduct_score(15)
        
        self.report.checks.append(check)

    def _check_xss_protection(self):
        """X-Content-Type-Options: Previene MIME Sniffing."""
        check = HeaderCheck("X-Content-Type-Options", "Evita carga de scripts con MIME incorrecto", "Medium")
        val = self.headers.get("x-content-type-options")
        
        if val == "nosniff":
            check.status = SecurityLevel.OK
            check.found_value = val
        else:
            check.status = SecurityLevel.WARNING # Modern browsers handle this better now, but still bad
            check.found_value = "MISSING"
            self.report.deduct_score(10)
        
        self.report.checks.append(check)

    def _check_server_leak(self):
        """Server / X-Powered-By: Fuga de información."""
        # Check Server header
        server = self.headers.get("server", "")
        powered = self.headers.get("x-powered-by", "")
        
        check = HeaderCheck("Info Leakage", "El servidor revela versiones de software", "Low")
        
        if len(server) > 10 or powered: # Simple heuristic
            check.status = SecurityLevel.WARNING
            check.found_value = f"Server: {server} | Powered: {powered}"
            self.report.deduct_score(5)
        else:
            check.status = SecurityLevel.OK
            check.found_value = "Clean"
        
        self.report.checks.append(check)

    def run(self):
        if not self._fetch_headers():
            return

        print(f"\n🔬 Iniciando Auditoría Arquitectónica para: {self.url}")
        print("-" * 60)
        
        # Pipeline de validaciones
        self._check_hsts()
        self._check_csp()
        self._check_clickjacking()
        self._check_xss_protection()
        self._check_server_leak()
        
        # Output
        print(f"{'CABECERA':<30} | {'ESTADO':<10} | {'DETALLE'}")
        print("-" * 60)
        
        for check in self.report.checks:
            print(f"{check.header_name:<30} | {check.status.value:<10} | {check.found_value}")

        print("-" * 60)
        print(f"\n📊 SECURITY SCORE: {self.report.score}/100")
        
        if self.report.score < 50:
            print("\n💀 CONCLUSIÓN: La seguridad es INEXISTENTE. Requiere intervención inmediata.")
        elif self.report.score < 80:
            print("\n⚠️ CONCLUSIÓN: Nivel aceptable pero con riesgos significativos.")
        else:
            print("\n🛡️ CONCLUSIÓN: Buena postura de seguridad.")

if __name__ == "__main__":
    auditor = EnterpriseAuditor(TARGET_URL)
    auditor.run()