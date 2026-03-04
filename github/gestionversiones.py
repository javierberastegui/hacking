import subprocess
import os
from dataclasses import dataclass
from typing import List, Optional, Callable, Any
from functools import wraps
from contextlib import contextmanager

# --- Decoradores para Lógica Transversal ---

def terminal_logger(func: Callable) -> Callable:
    """Decorador para trazar la ejecución de comandos de arquitectura."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        repo = args[1] if len(args) > 1 else "Unknown"
        print(f"🚀 [GIT-SYNC] Ejecutando operación en: {repo}...")
        try:
            result = func(*args, **kwargs)
            print(f"✅ [SUCCESS] Operación finalizada en {repo}.")
            return result
        except Exception as e:
            print(f"❌ [ERROR] Fallo crítico en {repo}: {e}")
            return None
    return wrapper

# --- Estructuras de Datos Estrictas ---

@dataclass(frozen=True)
class RepoStatus:
    path: str
    has_changes: bool
    untracked: bool

# --- Núcleo del Plugin ---

class GitManager:
    def __init__(self, base_path: str, repos: List[str]):
        self.base_path = os.path.expanduser(base_path)
        self.repos = repos

    @contextmanager
    def _change_dir(self, path: str):
        """Context Manager para asegurar el salto de directorios seguro."""
        old_dir = os.getcwd()
        os.chdir(path)
        try:
            yield
        finally:
            os.chdir(old_dir)

    def _run_git(self, args: List[str]) -> str:
        """Encapsulamiento de ejecución de procesos."""
        result = subprocess.run(
            ["git"] + args, 
            capture_output=True, 
            text=True, 
            check=True
        )
        return result.stdout.strip()

    @terminal_logger
    def sync_repo(self, repo_name: str) -> None:
        repo_path = os.path.join(self.base_path, repo_name)
        
        if not os.path.exists(repo_path):
            raise FileNotFoundError(f"El directorio {repo_path} no existe.")

        with self._change_dir(repo_path):
            # 1. Pull previo (Sincronización obligatoria)
            self._run_git(["pull", "origin", "main"]) # O la rama que uses
            
            # 2. Comprobar cambios
            status = self._run_git(["status", "--porcelain"])
            
            if not status:
                print(f"✨ {repo_name} está limpio. Nada que subir.")
                return

            # 3. Flujo de subida
            print(f"📦 Cambios detectados en {repo_name}:")
            print(status)
            
            commit_msg = input(f"💬 Comentario para {repo_name}: ")
            if not commit_msg.strip():
                commit_msg = "Auto-sync update"

            self._run_git(["add", "."])
            self._run_git(["commit", "-m", commit_msg])
            self._run_git(["push", "origin", "main"])

    def run_all(self) -> None:
        """Generador para procesar repositorios de forma eficiente."""
        for repo in self.repos:
            self.sync_repo(repo)

# --- Punto de Entrada ---

if __name__ == "__main__":
    # Configuración profesional: Lista de tus directorios según la imagen
    MY_REPOS = ["control-hogar", "econom-a", "hacking"]
    # En WSL, asegúrate de que la ruta sea la correcta (ej: ~/repos/)
    BASE_DIR = "~/tu_ruta_base_de_repos" 

    manager = GitManager(BASE_DIR, MY_REPOS)
    manager.run_all()