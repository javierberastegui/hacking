import time
import requests
from dataclasses import dataclass, asdict
from typing import Dict, Any, Generator, Optional, Callable
from contextlib import contextmanager
from stem import Signal
from stem.control import Controller

@dataclass(frozen=True)
class NetworkIdentity:
    """Estructura de datos para la identidad de red actual."""
    ip: str
    country: str
    city: str
    isp: str
    is_tor: bool = True

    def __str__(self) -> str:
        return (f"🌐 [IP]: {self.ip} | 📍 [Loc]: {self.city}, {self.country} "
                f"| 🏢 [ISP]: {self.isp}")

class TorIdentityService:
    """
    Servicio de alto nivel para la gestión y auditoría de circuitos Tor.
    """
    
    def __init__(self, control_port: int = 9051, proxy_port: int = 9050):
        self._control_port = control_port
        # Usamos socks5h para forzar la resolución DNS remota a través de Tor
        self._proxy_url = f"socks5h://127.0.0.1:{proxy_port}"
        self._api_url = "http://ip-api.com/json/"

    @contextmanager
    def _establish_control(self) -> Generator[Controller, None, None]:
        """Context Manager para asegurar la limpieza del socket de control."""
        try:
            with Controller.from_port(port=self._control_port) as controller:
                controller.authenticate() # Usa CookieAuth configurada en tu torrc
                yield controller
        except Exception as e:
            raise ConnectionError(f"Fallo en el puerto de control: {e}")

    def fetch_current_identity(self) -> NetworkIdentity:
        """Audita la IP pública actual a través del túnel SOCKS5h."""
        proxies = {'http': self._proxy_url, 'https': self._proxy_url}
        try:
            response = requests.get(self._api_url, proxies=proxies, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            return NetworkIdentity(
                ip=data.get('query', 'N/A'),
                country=data.get('country', 'N/A'),
                city=data.get('city', 'N/A'),
                isp=data.get('isp', 'N/A')
            )
        except Exception as e:
            print(f"[-] Error auditando la red: {e}")
            return NetworkIdentity("0.0.0.0", "Unknown", "Unknown", "Unknown", False)

    def get_rotator(self) -> Callable[[], NetworkIdentity]:
        """
        Closure avanzado que encapsula la lógica de rotación de identidad.
        Retorna una función que al ejecutarse cambia la IP y devuelve la nueva info.
        """
        def rotate() -> NetworkIdentity:
            with self._establish_control() as controller:
                if not controller.is_newnym_available():
                    wait_time = controller.get_newnym_wait()
                    print(f"[!] Límite de Tor alcanzado. Esperando {wait_time:.1f}s...")
                    time.sleep(wait_time)
                
                controller.signal(Signal.NEWNYM)
                print("[*] Señal NEWNYM enviada. Reconstruyendo circuito...")
                time.sleep(3) # Delay para estabilizar el nuevo nodo de salida
                return self.fetch_current_identity()
        
        return rotate

# --- Interfaz de Usuario (UI) ---

def main() -> None:
    # Instanciamos la arquitectura
    service = TorIdentityService()
    rotate_ip = service.get_rotator()

    print("--- 🛡️ Tor Identity Manager Pro ---")
    
    while True:
        print("\n[Menú Principal]")
        print("1. 👁️  Ver Identidad Actual")
        print("2. 🔄  Rotar Identidad (Nueva IP)")
        print("3. 🚪  Salir")
        
        choice = input("\n[?] Selección: ")

        if choice == "1":
            print("[*] Consultando rastro digital...")
            print(service.fetch_current_identity())
            
        elif choice == "2":
            nueva_id = rotate_ip()
            print(f"[+] Nueva Identidad Confirmada:")
            print(nueva_id)
            
        elif choice == "3":
            print("Cerrando sesión. Mantente bajo el radar...")
            break
        else:
            print("[-] No me vaciles, mete una opción de verdad.")

if __name__ == "__main__":
    main()