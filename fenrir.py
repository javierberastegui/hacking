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
from typing import List, Optional, Dict, Any, Callable
from enum import Enum, auto
from functools import wraps
from http.cookies import SimpleCookie
from yarl import URL

# ==============================================================================
#  🛠️ CONFIGURACIÓN & UTILS
# ==============================================================================

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("FENRIR")

class Colors:
    RED, GREEN, YELLOW, CYAN, RESET, BOLD = "\033[91m", "\033[92m", "\033[93m", "\033[96m", "\033[0m", "\033[1m"

def colorize(text: str, color: str) -> str: return f"{color}{text}{Colors.RESET}"

class TargetType(Enum):
    WORDPRESS = auto()
    PRESTASHOP = auto()
    GENERIC = auto()

@dataclass
class TargetConfig:
    base_url: str
    type: TargetType
    user_agent: str = "Fenrir/3.0-ContextAware"
    timeout: int = 15

class FenrirEngine:
    def __init__(self, config: TargetConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        jar = aiohttp.CookieJar(unsafe=True)
        self.session = aiohttp.ClientSession(
            base_url=self.config.base_url,
            connector=aiohttp.TCPConnector(ssl=False),
            cookie_jar=jar,
            headers={"User-Agent": self.config.user_agent},
            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
        )
        return self

    async def __aexit__(self, *args):
        if self.session: await self.session.close()

    def inject_raw_cookie(self, raw_cookie: str):
        if not self.session: return
        print(colorize("💉 Inyectando Cookies...", Colors.YELLOW))
        try:
            url_obj = URL(self.config.base_url)
            cookie = SimpleCookie()
            raw_cookie = raw_cookie.replace("Cookie: ", "").strip()
            
            # Auto-Correction para WordPress
            if self.config.type == TargetType.WORDPRESS and "wordpress_logged_in" not in raw_cookie and "=" not in raw_cookie:
                 print(colorize("⚠️ ALERTA: Detectado valor suelto en modo WP.", Colors.RED))
                 print("   Debes copiar el NOMBRE de la cookie que empieza por 'wordpress_logged_in_...'")
                 return

            if "=" not in raw_cookie:
                print(colorize("⚠️ Formato incorrecto. Se requiere Nombre=Valor", Colors.RED))
                raw_cookie = f"PHPSESSID={raw_cookie}"

            cookie.load(raw_cookie)
            for key, morsel in cookie.items():
                self.session.cookie_jar.update_cookies({key: morsel.value}, response_url=url_obj)
            
            print(colorize(f"✅ Cookies cargadas: {list(cookie.keys())}", Colors.GREEN))
        except Exception as e:
            print(colorize(f"❌ Error inyectando cookies: {e}", Colors.RED))

    async def fuzz_endpoints(self, wordlist: List[str]):
        print(colorize(f"\n🐕 RASTREANDO ({self.config.type.name}) con Validación Positiva...", Colors.BOLD))
        tasks = [self._check_endpoint(path) for path in wordlist]
        await asyncio.gather(*tasks)

    async def _check_endpoint(self, path: str):
        if not self.session: return
        try:
            async with self.session.get(path, allow_redirects=True) as resp:
                content = await resp.text()
                
                # --- VALIDACIÓN POSITIVA (SOLO ACEPTAMOS SI VEMOS ESTO) ---
                # Si no encontramos estas palabras, asumimos que el server miente (Soft 404)
                
                is_valid = False
                found_keyword = ""

                if self.config.type == TargetType.WORDPRESS:
                    # Palabras CLAVE que solo salen si eres Admin en WP
                    wp_success_keys = ["wp-admin-bar", "dashicons", "Howdy", "Hola,", "Cerrar sesión", "Log Out", "Escritorio"]
                    for k in wp_success_keys:
                        if k in content:
                            is_valid = True; found_keyword = k; break
                            
                elif self.config.type == TargetType.PRESTASHOP:
                    # Palabras CLAVE de PrestaShop Admin
                    ps_success_keys = ["logout", "employee_box", "class=\"bootstrap\"", "PrestaShop", "Cerrar sesión"]
                    for k in ps_success_keys:
                        if k in content and "login" not in content.lower(): # Evitamos falsos positivos del login page
                            is_valid = True; found_keyword = k; break

                if is_valid:
                    print(f"  -> {colorize('🔥 ¡DENTRO! [CONFIRMADO]', Colors.GREEN)} {path} (Visto: '{found_keyword}')")
                elif resp.status == 200:
                    # Si es 200 pero no vemos las llaves, es un falso positivo o un login page
                    if "wp-login" in str(resp.url) or "AdminLogin" in str(resp.url):
                         print(f"  -> {colorize('ACCESIBLE [LOGIN]', Colors.YELLOW)} {path}")
                    else:
                         # Silenciamos los Soft 404 para no confundirte
                         pass 

        except: pass

async def main():
    print(colorize("\n🐺 FENRIR v3.0 - CONTEXT AWARE 🐺\n", Colors.RED))

    base_input = input(">> URL Base: ").strip()
    if not base_input.startswith("http"): base_input = f"http://{base_input}"
    if not base_input.endswith("/"): base_input += "/"
    
    print("\n[1] WordPress")
    print("[2] PrestaShop")
    t_choice = input(">> Tecnología Objetivo: ").strip()
    
    t_type = TargetType.GENERIC
    wordlist = []
    
    if t_choice == '1': 
        t_type = TargetType.WORDPRESS
        # Rutas reales de WP
        wordlist = ["wp-admin/", "wp-admin/index.php", "wp-admin/profile.php", "wp-admin/users.php", "wp-admin/options-general.php"]
    elif t_choice == '2': 
        t_type = TargetType.PRESTASHOP
        # Rutas reales de PrestaShop (Backoffice suele cambiar, hay que adivinarlo o saberlo)
        wordlist = ["admin", "backoffice", "dashboard", "administration", "adm", "index.php?controller=AdminDashboard"]
    
    config = TargetConfig(base_url=base_input, type=t_type)

    async with FenrirEngine(config) as engine:
        print(f"\n{Colors.YELLOW}👉 Opción 3: INYECCIÓN DE COOKIE (SOLO ESTO FUNCIONARÁ SI TIENES MFA O PLUGINS){Colors.RESET}")
        print(f"{Colors.CYAN}   Ej WP: wordpress_logged_in_xxxx=valor...{Colors.RESET}")
        
        raw = input(">> Pega la Cookie (Nombre=Valor): ").strip()
        engine.inject_raw_cookie(raw)

        await engine.fuzz_endpoints(wordlist)

if __name__ == "__main__":
    if sys.platform == 'win32': asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())