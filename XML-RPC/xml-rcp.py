import requests
import time
import logging
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable
from functools import wraps

# Configuración de Logging 'Pro'
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [AUDIT] - %(message)s')
logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class TargetConfig:
    """
    Immutable configuration for the audit target.
    Safety first: We treat configurations as constant truth.
    """
    url: str
    timeout: int = 10
    user_agent: str = "SecurityAudit/1.0 (Authorized Audit)"

    @property
    def endpoint(self) -> str:
        return f"{self.url.rstrip('/')}/xmlrpc.php"

def audit_timer(func: Callable) -> Callable:
    """
    Decorator to measure execution time of audit methods.
    Crucial for detecting Time-Based Blind SQLi or sluggish server responses.
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start_time = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            elapsed = time.perf_counter() - start_time
            logger.debug(f"Execution of '{func.__name__}' took {elapsed:.4f}s")
    return wrapper

class XMLRPCAuditor:
    """
    Architectural Pattern: Service Object.
    Encapsulates all logic related to XML-RPC interaction via a clean API.
    """
    
    def __init__(self, config: TargetConfig) -> None:
        self._config = config
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": self._config.user_agent})

    @audit_timer
    def verify_system_methods(self) -> bool:
        """
        Sends a 'system.listMethods' payload to verify if the interface is active.
        This is a NON-DESTRUCTIVE check.
        """
        payload = """
        <methodCall>
          <methodName>system.listMethods</methodName>
          <params></params>
        </methodCall>
        """
        
        try:
            logger.info(f"Probing XML-RPC endpoint: {self._config.endpoint}")
            response = self._session.post(
                self._config.endpoint, 
                data=payload, 
                timeout=self._config.timeout
            )
            
            if response.status_code == 200 and '<methodResponse>' in response.text:
                self._parse_and_report(response.text)
                return True
            
            logger.warning(f"XML-RPC endpoint found but not responsive as expected (Status: {response.status_code})")
            return False

        except requests.RequestException as e:
            logger.error(f"Network error during audit: {str(e)}")
            return False

    def _parse_and_report(self, response_text: str) -> None:
        """
        Internal method to analyze the response.
        """
        # A simple check for dangerous methods often left open
        dangerous_methods = ['pingback.ping', 'wp.getUsersBlogs']
        found_dangers = [m for m in dangerous_methods if m in response_text]
        
        logger.info("✅ XML-RPC is ACTIVE and responding.")
        if found_dangers:
            logger.critical(f"⚠️  CRITICAL: Dangerous methods exposed: {found_dangers}")
            logger.info("   -> This confirms vulnerability to DDoS amplification and Brute Force.")
        else:
            logger.info("   -> Methods listed, but standard dangerous ones might be disabled (unlikely).")

# --- Execution Entry Point ---
if __name__ == "__main__":
    # Instanciamos con datos tipados, nada de strings sueltos
    target = TargetConfig(url="https://farmaciatenerife.com")
    auditor = XMLRPCAuditor(config=target)
    
    print("--- STARTING ARCHITECTURAL AUDIT ---")
    is_vulnerable = auditor.verify_system_methods()
    print(f"--- AUDIT FINISHED. VULNERABLE: {is_vulnerable} ---")