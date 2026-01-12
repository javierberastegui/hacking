import subprocess
import sys
import shutil
import os
import time
from typing import Final, List, Iterator, Optional, Generator, Any
from dataclasses import dataclass, field
from functools import wraps
from datetime import datetime

# --- LIBRERÍAS DE UI (Nivel Dios) ---
try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
    from rich.panel import Panel
    from rich.text import Text
    from rich.theme import Theme
except ImportError:
    print("❌ Error: Falta el arsenal. Ejecuta: pip install rich")
    sys.exit(1)

# Configuración de tema personalizado para una estética 'Hacker' pero legible
custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold green",
    "phase": "bold magenta"
})
console = Console(theme=custom_theme)

# --- 1. Decoradores ---

def audit_execution(phase_name: str):
    """Mide rendimiento y gestiona el ciclo de vida sin ensuciar la UI."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Ya no hacemos print aquí para no romper la barra de progreso
            start_time = time.perf_counter()
            try:
                return func(*args, **kwargs)
            except Exception as e:
                console.print(f"[error]💥 Excepción en {phase_name}: {e}[/error]")
                raise
            finally:
                elapsed = time.perf_counter() - start_time
                # Este log saldrá limpio al final de la fase
                console.print(f"[dim]🏁 {phase_name} finalizado en {elapsed:.2f}s[/dim]")
        return wrapper
    return decorator

# --- 2. Estructuras de Datos ---

@dataclass(frozen=True)
class PhaseConfig:
    name: str
    level: int
    risk: int
    flags: List[str] = field(default_factory=list)

    @property
    def cmd_signature(self) -> str:
        return f"L{self.level}::R{self.risk}::{self.name}"

# --- 3. El Core: Mjolnir Engine ---

class SqlMapArchitect:
    def __init__(self, target_url: str):
        self.target: Final[str] = self._sanitize_target(target_url)
        self._binary: Final[Optional[str]] = shutil.which("sqlmap")
        
        if not self._binary:
            raise EnvironmentError("❌ SQLMap no encontrado. Instálalo.")

    @staticmethod
    def _sanitize_target(url: str) -> str:
        return "".join(ch for ch in url if ord(ch) >= 32).strip()

    def _strategy_generator(self) -> Generator[PhaseConfig, None, None]:
        yield PhaseConfig("Infiltración Ghost (Recon)", 1, 1, ["--smart", "--batch", "--random-agent", "--dbs"])
        yield PhaseConfig("Asalto Táctico (Heurística)", 3, 2, ["--batch", "--tamper=space2comment", "--threads=5"])
        yield PhaseConfig("Demolición Berserker (Full Noise)", 5, 3, ["--batch", "--level=5", "--risk=3", "--random-agent"])

    def _execute_subprocess(self, cmd: List[str]) -> Iterator[str]:
        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1, universal_newlines=True
        )
        if process.stdout:
            for line in process.stdout:
                yield line.strip()
        process.wait()
        if process.returncode != 0:
            # No lanzamos error aquí para permitir que el script maneje el fallo visualmente
            yield f"ERROR_CODE_{process.returncode}"

    def engage(self) -> None:
        console.print(Panel(f"[bold blue]TARGET LOCKED:[/bold blue] [white]{self.target}[/white]", expand=False))

        for phase in self._strategy_generator():
            self._run_phase_with_ui(phase)

    @audit_execution("Phase Runner")
    def _run_phase_with_ui(self, phase: PhaseConfig) -> None:
        command = [self._binary, "-u", self.target] + \
                  [f"--level={phase.level}", f"--risk={phase.risk}"] + phase.flags

        console.print(f"\n[phase]🚀 INICIANDO FASE: {phase.cmd_signature}[/phase]")

        # --- AQUÍ ESTÁ LA MAGIA VISUAL ---
        # Usamos 'Progress' de rich para crear una barra indeterminada (pulse)
        with Progress(
            SpinnerColumn("aesthetic"),      # Spinner guapo
            TextColumn("[bold blue]{task.description}"), # Qué está pasando
            BarColumn(bar_width=None),       # La barra que rebota (pulse)
            TimeElapsedColumn(),             # Tiempo transcurrido
            transient=True,                  # Desaparece al acabar para limpiar pantalla
            console=console
        ) as progress:
            
            # Tarea "indeterminada" (total=None)
            task_id = progress.add_task(f"Inicializando {phase.name}...", total=None)

            try:
                for log_line in self._execute_subprocess(command):
                    # Actualizamos la descripción de la barra con la última línea de log real
                    # Limpiamos un poco el texto para que quepa
                    clean_log = log_line.replace("[INFO]", "").replace("[WARNING]", "⚠️").strip()
                    if len(clean_log) > 80: clean_log = clean_log[:77] + "..."
                    
                    progress.update(task_id, description=f"[cyan]{clean_log}")

                    # Filtros de eventos importantes para imprimir persistente
                    if "CRITICAL" in log_line or "ERROR" in log_line:
                        console.print(f"[error]🔴 {log_line}[/error]")
                        # Si es un error de parámetros, paramos esta fase pronto
                        if "no parameter" in log_line or "no forms" in log_line:
                            progress.stop()
                            break
                            
                    elif "vulnerable" in log_line.lower() or "injection" in log_line.lower():
                        console.print(Panel(f"[success]🎉 EUREKA: {log_line}[/success]"))
                    
                    elif "database management system" in log_line.lower():
                         console.print(f"[success]✅ DBMS DETECTADO: {log_line}[/success]")

            except Exception as e:
                console.print(f"[error]⚠️ Error de ejecución: {e}[/error]")

# --- 4. Entry Point ---

def main():
    os.system('clear' if os.name == 'posix' else 'cls')
    
    # Header con estilo usando Rich
    title = Text("🔨 LOKKY'S MJÖLNIR - ARCHITECT UI EDITION v3.0", justify="center", style="bold white on blue")
    console.print(Panel(title))

    try:
        target = console.input("[bold green]🔥 Introduce URL Objetivo: [/bold green]").strip()
        if not target:
            console.print("[bold red]😒 Venga, no tengo todo el día. Dame una URL.[/bold red]")
            sys.exit(1)
        
        bot = SqlMapArchitect(target)
        bot.engage()

    except KeyboardInterrupt:
        console.print("\n[bold yellow]👋 Abortando misión. Cambio y corto.[/bold yellow]")
    except Exception as e:
        console.print(f"\n[bold red]💥 Error fatal: {e}[/bold red]")

if __name__ == "__main__":
    main()