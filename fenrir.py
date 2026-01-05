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
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Callable, Generator, Coroutine
from enum import Enum, auto
from functools import wraps
from http.cookies import SimpleCookie

# ==============================================================================
#  🛠️ CONFIGURACIÓN & UTILS
# ==============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("FENRIR")

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
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

def async_timer(func: Callable[..., Coroutine]) -> Callable[..., Coroutine]:
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = await func(*args, **kwargs)
        end = time.perf_counter()
        if (end - start) * 1000 > 1000:
            logger.debug(f"Slow ops: {func.__name__}")
        return result
    return wrapper

# --- DATA STRUCTURES ---

class AuthMode(Enum):
    NONE = auto()
    JWT = auto()
    COOKIE = auto()

@dataclass(frozen=True)
class TargetConfig:
    base_url: str
    user_agent: str = "Fenrir/2.1-SessionHijacker"
    timeout: int = 15

@dataclass
class AuthResult:
    mode: AuthMode
    artifact: str
    success: bool

# ==============================================================================
#  🧠 BUSINESS LOGIC: LOW LEVEL
# ==============================================================================

class JWTManipulator:
    @staticmethod
    def b64url_decode(data: str) -> bytes:
        padding = 4 - (len(data) % 4)
        if padding != 4: data += "=" * padding
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
#  🐺 CORE ENGINE: FENRIR
# ==============================================================================

class FenrirEngine:
    def __init__(self, config: TargetConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self._token: Optional[str] = None
        self.auth_mode: AuthMode = AuthMode.NONE

    async def __aenter__(self):
        jar = aiohttp.CookieJar(unsafe=True)
        connector = aiohttp.TCPConnector(limit=50, ssl=False)
        self.session = aiohttp.ClientSession(
            base_url=self.config.base_url,
            connector=connector,
            cookie_jar=jar,
            headers={"User-Agent": self.config.user_agent},
            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session: await self.session.close()

    @property
    def token(self) -> str:
        return self._token if self._token else ""

    @token.setter
    def token(self, value: str):
        self._token = value
        if self.session and value:
            self.session.headers.update({"Authorization": f"Bearer {value}"})
            self.auth_mode = AuthMode.JWT

    def inject_raw_cookie(self, raw_cookie: str):
        """
        Parsea una cadena de cookies cruda (tipo navegador) y la inyecta.
        """
        if not self.session: return
        print(colorize("💉 Inyectando Cookies...", Colors.YELLOW))
        try:
            cookie = SimpleCookie()
            cookie.load(raw_cookie)
            for key, morsel in cookie.items():
                self.session.cookie_jar.update_cookies({key: morsel.value}, response_url=self.config.base_url)
            
            self.auth_mode = AuthMode.COOKIE
            print(colorize("✅ Session Hijacking completado.", Colors.GREEN))
        except Exception as e:
            print(colorize(f"❌ Error parseando cookies: {e}", Colors.RED))

    @async_timer
    async def pre_flight_check(self) -> bool:
        if not self.session: return False
        try:
            async with self.session.get("/") as resp:
                print(colorize(f"✅ Host activo: {resp.status}", Colors.GREEN))
                return True
        except: return False

    @audit_log
    async def hunt_credentials(self, login_path: str, creds: Dict[str, str]) -> AuthResult:
        if not self.session: return AuthResult(AuthMode.NONE, "", False)
        print(colorize(f"🕵️  Intentando login en: {login_path}", Colors.YELLOW))
        
        try:
            # Estrategia POST Form Data (Estándar WP)
            async with self.session.post(login_path, data=creds) as resp:
                 if self.session.cookie_jar.filter_cookies(self.config.base_url):
                    print(colorize("✅ [COOKIE] Sesión capturada.", Colors.GREEN))
                    return AuthResult(AuthMode.COOKIE, "SessionCookie", True)
                 
                 # Check HTML for Token
                 text = await resp.text()
                 match = re.search(r'eyJ[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+', text)
                 if match: return AuthResult(AuthMode.JWT, match.group(0), True)

        except Exception as e:
            logger.error(f"Error auth: {e}")
        
        return AuthResult(AuthMode.NONE, "", False)

    async def fuzz_endpoints(self, wordlist: List[str]) -> List[str]:
        print(colorize(f"\n🐕 RASTREANDO ({self.auth_mode.name})...", Colors.BOLD))
        tasks = [self._check_endpoint(path) for path in wordlist]
        results = await asyncio.gather(*tasks)
        found = [r for r in results if r is not None]
        
        if not found:
            print(colorize("🤷 Sin accesos. (¿Seguro que la cookie es de Admin?)", Colors.CYAN))
        return found

    async def _check_endpoint(self, path: str) -> Optional[str]:
        if not self.session: return None
        try:
            # allow_redirects=True para seguir redirecciones de WP
            async with self.session.get(path, allow_redirects=True) as resp:
                # Si nos devuelve 200 y NO nos ha redirigido al login, es válido
                if resp.status == 200 and "wp-login" not in str(resp.url):
                    print(f"  -> {colorize('ACCESIBLE [200]', Colors.GREEN)} {path}")
                    return path
                elif resp.status == 403:
                    print(f"  -> {colorize('PROTEGIDO [403]', Colors.YELLOW)} {path}")
        except: pass
        return None

    # ... [ATAQUES JWT SE MANTIENEN IGUAL PERO OCULTOS POR BREVEDAD] ...
    async def execute_attacks(self, targets: List[str]):
        if self.auth_mode == AuthMode.COOKIE:
            print(colorize("\nℹ️ Modo Cookie: Ataques JWT omitidos. Auditoría de acceso realizada.", Colors.CYAN))
            return
        # (Aquí iría la lógica de ataque JWT si hubiese token)

# ==============================================================================
#  🏁 MAIN
# ==============================================================================

async def main():
    print(colorize("\n🐺 FENRIR v2.1 - SESSION HIJACKER 🐺\n", Colors.RED))

    # OJO AQUÍ: Asegúrate de poner la URL base SIN /wp-login.php
    base_input = input(">> URL Base (ej: https://web.com/carpeta): ").strip()
    if not base_input.startswith("http"): base_input = f"http://{base_input}"
    
    config = TargetConfig(base_url=base_input)

    async with FenrirEngine(config) as engine:
        if not await engine.pre_flight_check():
            print("❌ Host caído."); sys.exit(1)

        print("\n[1] Auto-Login (Poco fiable en WP moderno)")
        print("[2] Pegar Token JWT")
        print("[3] Inyección de Cookie (Bypass Total)")
        choice = input(">> Opción: ").strip()

        if choice == '1':
            user = input("User: ")
            pwd = input("Pass: ")
            path = input(">> Login Path: ").strip()
            res = await engine.hunt_credentials(path, {"log": user, "pwd": pwd, "wp-submit": "Log In"})
            if res.success: engine.auth_mode = res.mode
            else: print("❌ Fallo."); sys.exit(1)

        elif choice == '2':
            t = input(">> Token: ").strip()
            engine.token = t

        elif choice == '3':
            print(f"\n{Colors.YELLOW}👉 Ve al navegador -> F12 -> Red -> Petición cualquiera -> Copia 'Cookie: ...'{Colors.RESET}")
            raw = input(">> Pega la cadena 'Cookie': ").strip()
            # Limpieza básica por si copias "Cookie: " al principio
            if raw.lower().startswith("cookie:"): raw = raw[7:].strip()
            engine.inject_raw_cookie(raw)

        # Discovery
        targets = await engine.fuzz_endpoints([
            "/wp-admin/", "/wp-admin/users.php", "/wp-admin/options-general.php", 
            "/wp-json/wp/v2/users", "/admin", "/dashboard"
        ])
        
        await engine.execute_attacks(targets)

if __name__ == "__main__":
    if sys.platform == 'win32': asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())