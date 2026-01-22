import time
import sys
import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Generator, Callable, ContextManager, Optional, Type
from functools import wraps
from types import TracebackType

# --- CONFIGURATION LAYER (Data Structure & Assets) ---
@dataclass(frozen=True)
class PomodoroConfig:
    """
    Immutable configuration object.
    Now includes motivation assets using default_factory for mutable defaults.
    """
    focus_duration: int = 25
    break_duration: int = 5
    cycles: int = 4
    app_name: str = "ArchitectFocus CLI v2.0 (Emotion Enabled)"
    # Assets for Positive Reinforcement Module
    work_quotes: list[str] = field(default_factory=lambda: [
        "¡Dale duro, eres una máquina! 🚀",
        "El éxito es la suma de pequeños esfuerzos. ¡Tú puedes! 💪",
        "Concéntrate. La recompensa es enorme. 🧠⚡",
        "No te rindas, cada segundo cuenta. 🏆",
        "Modo 'Deep Work' activado. ¡A picar piedra! 🦍🔥",
        "Haz que tu yo del futuro esté orgulloso. ✨"
    ])
    break_quotes: list[str] = field(default_factory=lambda: [
        "Respira hondo. Te lo has ganado. 😌🍃",
        "Estira las piernas, hidrátate y recarga energía. 🔋",
        "Desconecta el cerebro para reconectar mejor. 🧘‍♂️✨",
        "Un cafecito rápido y volvemos a la carga. ☕🥐",
        "¡Muy bien hecho! Disfruta estos minutos. 🎉"
    ])

# --- DECORATOR LAYER ---
def audit_session(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args, **kwargs):
        print(f"\n[📜 SYSTEM LOG] Initializing: {func.__name__.upper()} at {datetime.now().strftime('%H:%M:%S')}")
        try:
            return func(*args, **kwargs)
        finally:
            print(f"[📜 SYSTEM LOG] Finalized: {func.__name__.upper()} at {datetime.now().strftime('%H:%M:%S')}\n")
    return wrapper

# --- CORE LOGIC LAYER ---
class PomodoroSession:
    def __init__(self, config: PomodoroConfig):
        self._config = config
        self._is_active: bool = False
        # Functional Injection: Standard system notifier
        self._notifier: Callable[[str], None] = self._notification_factory(prefix="🔔 STATUS")
        # Functional Injection: Emotional support closures
        self._work_motivator = self._motivator_factory(self._config.work_quotes, icon="🔥")
        self._break_motivator = self._motivator_factory(self._config.break_quotes, icon="🌿")

    def __enter__(self) -> "PomodoroSession":
        self._is_active = True
        print(f"🚀 --- {self._config.app_name} INITIALIZED --- 🚀")
        print("Prepara tu entorno. Vamos a ser productivos hoy.\n")
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self._is_active = False
        if exc_type:
            print(f"\n💀 [ERROR] Session interrupted abruptly: {exc_value}")
        print("\n🛑 --- Session Teardown Complete. ¡Buen trabajo hoy! --- 👋")

    @staticmethod
    def _notification_factory(prefix: str) -> Callable[[str], None]:
        """Standard operational messages."""
        def _notify(message: str) -> None:
            print(f"{prefix}: {message}")
        return _notify

    @staticmethod
    def _motivator_factory(quote_list: list[str], icon: str) -> Callable[[], None]:
        """
        CLOSURE V2: Creates a specialized motivator function with encapsulated state 
        (the specific list and icon). It randomly selects a quote.
        """
        def _motivate() -> None:
            # Random selection happens inside the closure execution
            quote = random.choice(quote_list)
            print(f"\n{icon * 3} ¡{quote.upper()}! {icon * 3}\n")
        return _motivate

    def _timer_generator(self, minutes: int) -> Generator[str, None, None]:
        """Non-blocking time generator."""
        seconds = minutes * 60
        while seconds > 0:
            m, s = divmod(seconds, 60)
            yield f"{m:02d}:{s:02d}"
            time.sleep(1)
            seconds -= 1
        yield "00:00"

    @audit_session
    def start_cycle(self) -> None:
        """Orchestrates the Pomodoro cycles with injected motivation."""
        total_cycles = self._config.cycles
        
        for i in range(1, total_cycles + 1):
            self._notifier(f"Starting Cycle {i}/{total_cycles}")
            
            # --- FOCUS PHASE ---
            self._work_motivator() # Inject dopamine
            for timer in self._timer_generator(self._config.focus_duration):
                # Enhanced visual feedback in the loop
                sys.stdout.write(f"\r🧐 ENFOCADO: {timer} | ¡Dale caña! ⌨️💨   ")
                sys.stdout.flush()
            
            print() # Newline
            self._notifier("Time's up! Focus phase complete.")

            # --- BREAK PHASE ---
            if i < total_cycles:
                self._break_motivator() # Inject serotonin
                for timer in self._timer_generator(self._config.break_duration):
                    sys.stdout.write(f"\r😴 RELAX: {timer} | Recargando... 🛁🦆   ")
                    sys.stdout.flush()
                print()
                self._notifier("Break over. Get ready.")
            else:
                 print("\n🎉✨ ¡SEACABÓ! Has completado todos los ciclos. Eres increíble. ✨🎉")

# --- EXECUTION ENTRY POINT ---
if __name__ == "__main__":
    # Configuración: 25min trabajo, 5min descanso, 4 ciclos.
    config = PomodoroConfig(focus_duration=25, break_duration=5, cycles=4)
    
    try:
        with PomodoroSession(config) as session:
            session.start_cycle()
    except KeyboardInterrupt:
        # Catching Ctrl+C cleanly
        print("\n\n🙉 [USER] ¡Ups! Cancelado manualmente. ¡Hasta la próxima!")