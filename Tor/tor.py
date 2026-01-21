import time
import requests
import logging
import os
from dataclasses import dataclass
from typing import Optional, Any, Callable, TypeVar
from functools import wraps
from stem import Signal
from stem.control import Controller
from stem.util import log as stem_log
from dotenv import load_dotenv

# 1. Carga de Secretos (Fail Fast)
# Busca el archivo .env inmediatamente.
load_dotenv()

# 2. Configuración de Logging 'Pro'
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] ➤ %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("TorArchitect")
stem_log.get_logger().level = stem_log.logging.ERROR

T = TypeVar("T")

# 3. Gestión de Configuración Centralizada
@dataclass(frozen=True)
class AppConfig:
    """
    Patrón de configuración. Valida el entorno antes de arrancar.
    Si falta la password, explota controladamente aquí.
    """
    tor_password: str
    control_port: int = 9051
    socks_port: int = 9050

    @classmethod
    def load(cls) -> 'AppConfig':
        # Busca la variable exacta que definiste en tu .env
        pwd = os.getenv("TOR_CONTROL_PASSWORD")
        if not pwd:
            raise ValueError(
                "❌ FATAL: No se encontró 'TOR_CONTROL_PASSWORD'. "
                "Asegúrate de tener el archivo .env creado correctamente."
            )
        return cls(tor_password=pwd)

@dataclass(frozen=True)
class GeoIdentity:
    """Modelo inmutable para la identidad de red."""
    ip: str
    city: str
    region: str
    country: str
    loc: str
    org: str

class NetworkError(Exception):
    pass

def retry_policy(max_retries: int = 3, delay: int = 2) -> Callable:
    """Decorador para resiliencia (Exponential Backoff)."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    wait_time = delay * (2 ** attempt)
                    logger.warning(f"⚠️ Intento {attempt + 1}/{max_retries} fallido en {func.__name__}: {e}. Reintentando en {wait_time}s...")
                    time.sleep(wait_time)
                    last_exception = e
            logger.error(f"❌ Operación {func.__name__} muerta tras {max_retries} intentos.")
            raise last_exception if last_exception else NetworkError("Unknown error")
        return wrapper
    return decorator

class TorCircuitManager:
    """
    Controlador de infraestructura Tor.
    Implementa Context Manager para garantizar limpieza de sockets.
    """

    def __init__(self, password: str, control_port: int = 9051, socks_port: int = 9050):
        self._control_port = control_port
        self._password = password
        self._socks_port = socks_port
        self._controller: Optional[Controller] = None
        self._session = requests.Session()
        
        # Enrutamos TODAS las peticiones de esta sesión por SOCKS5h
        # (socks5h significa que el DNS también se resuelve por Tor, vital para anonimato)
        proxies = {
            'http': f'socks5h://127.0.0.1:{self._socks_port}',
            'https': f'socks5h://127.0.0.1:{self._socks_port}'
        }
        self._session.proxies.update(proxies)

    def __enter__(self) -> 'TorCircuitManager':
        try:
            self._controller = Controller.from_port(port=self._control_port)
            self._controller.authenticate(password=self._password)
            logger.info(f"✅ Conectado al Controlador Tor v{self._controller.get_version()}")
        except Exception as e:
            logger.critical(f"🔥 Error de conexión (Puerto {self._control_port}): {e}")
            raise
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._controller:
            self._controller.close()
            logger.info("🔒 Conexión con controlador cerrada.")

    @retry_policy(max_retries=3)
    def get_current_identity(self) -> GeoIdentity:
        """Verifica IP externa."""
        try:
            response = self._session.get("https://ipinfo.io/json", timeout=15)
            response.raise_for_status()
            data = response.json()
            
            return GeoIdentity(
                ip=data.get("ip", "Unknown"),
                city=data.get("city", "Unknown"),
                region=data.get("region", "Unknown"),
                country=data.get("country", "Unknown"),
                loc=data.get("loc", "Unknown"),
                org=data.get("org", "Unknown")
            )
        except requests.RequestException as e:
            raise NetworkError(f"Fallo de resolución DNS/HTTP: {e}")

    def rotate_identity(self) -> None:
        """Solicita nuevo circuito limpio (NEWNYM)."""
        if not self._controller:
            return
        
        logger.info("🔄 Solicitando nueva identidad a la red Tor...")
        self._controller.signal(Signal.NEWNYM)
        
        wait_time = self._controller.get_newnym_wait()
        time.sleep(wait_time) 
        logger.info("✨ Circuito renovado.")

    def kill_tor_process(self) -> None:
        """Mata el servicio Tor en el host."""
        if not self._controller:
            return
        logger.warning("💀 Enviando SIGTERM/SHUTDOWN a Tor...")
        self._controller.signal(Signal.SHUTDOWN)

# --- ENTRY POINT ---
if __name__ == "__main__":
    try:
        # 1. Cargar configuración segura
        config = AppConfig.load()
        
        # 2. Iniciar Gestor
        with TorCircuitManager(
            password=config.tor_password, 
            control_port=config.control_port,
            socks_port=config.socks_port
        ) as tor:
            
            # Estado Inicial
            identity = tor.get_current_identity()
            print(f"\n👻 ID INICIAL:\n   IP: {identity.ip}\n   Loc: {identity.city}, {identity.country}\n   ISP: {identity.org}\n")

            # Loop Interactivo
            while True:
                opcion = input("CMD [r=rotar | k=kill | q=quit] > ").lower().strip()
                
                if opcion == 'r':
                    tor.rotate_identity()
                    new_id = tor.get_current_identity()
                    print(f"\n🌍 NUEVA ID:\n   IP: {new_id.ip}\n   Loc: {new_id.city}, {new_id.country}\n   ISP: {new_id.org}\n")
                
                elif opcion == 'k':
                    confirm = input("¿Seguro que quieres matar el servicio Tor del sistema? (s/n): ")
                    if confirm.lower() == 's':
                        tor.kill_tor_process()
                        print("💀 Servicio detenido. Game over.")
                        break
                
                elif opcion == 'q':
                    print("👋 Saliendo...")
                    break
                
                else:
                    print("¿Qué dices? Usa [r], [k] o [q].")

    except ValueError as config_error:
        # Error limpio si falta el .env
        logger.critical(config_error)
    except KeyboardInterrupt:
        print("\nAbortado.")
    except Exception as e:
        logger.fatal(f"Crash inesperado: {e}")