import os
import shutil
import ast
import logging
from pathlib import Path
from typing import Generator, List, Optional, Callable, Any
from functools import wraps
from dataclasses import dataclass, field
import time

# --- Configuration & Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [ARCHITECT_FIX] - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# --- Data Structures (Pydantic-style dataclasses for zero dependencies) ---
@dataclass(frozen=True)
class ScanResult:
    """Immutable data object to hold scan findings."""
    filepath: Path
    issue_type: str
    line_number: int
    details: str

@dataclass
class ProjectHealthReport:
    """Aggregate report of the project status."""
    project_root: Path
    cleaned_caches: int = 0
    conflicts_found: List[ScanResult] = field(default_factory=list)
    syntax_errors: List[ScanResult] = field(default_factory=list)

    @property
    def is_healthy(self) -> bool:
        return not self.conflicts_found and not self.syntax_errors

# --- Decorators ---
def measure_performance(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to measure the execution time of critical maintenance tasks."""
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.perf_counter()
        logger.info(f"🚀 Starting routine: {func.__name__}...")
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            elapsed = time.perf_counter() - start_time
            logger.info(f"🏁 Routine {func.__name__} completed in {elapsed:.4f}s")
    return wrapper

# --- Context Managers ---
class ProjectScopeManager:
    """
    Context Manager to ensure we operate strictly within the project boundaries
    and handle file system permission errors gracefully.
    """
    def __init__(self, root_path: str = "."):
        self.root = Path(root_path).resolve()

    def __enter__(self) -> Path:
        if not self.root.exists():
            raise FileNotFoundError(f"Project root not found: {self.root}")
        logger.info(f"🛡️  Locking onto project scope: {self.root}")
        return self.root

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            logger.error(f"❌ Error during project operation: {exc_val}")
        # No suppression of exceptions, let them bubble up after logging

# --- Core Logic ---

class ProjectSanitizer:
    """
    Architectural component responsible for deep cleaning and static analysis
    of the codebase to resolve 'ghost' errors after git pulls.
    """
    
    def __init__(self, root_path: Path):
        self.root = root_path
        self.report = ProjectHealthReport(project_root=root_path)

    @property
    def _python_files(self) -> Generator[Path, None, None]:
        """Generator that yields all python files, respecting .gitignore conceptually."""
        for path in self.root.rglob("*.py"):
            if "venv" in path.parts or ".git" in path.parts:
                continue
            yield path

    @measure_performance
    def purge_bytecode(self) -> None:
        """
        Recursively annihilates __pycache__ directories and .pyc files.
        Forces Python to re-compile source code, eliminating stale execution paths.
        """
        logger.info("🧹 Initiating Bytecode Purge Protocols...")
        
        # Strategy: Remove directories first
        for path in self.root.rglob("__pycache__"):
            if "venv" in path.parts: continue
            try:
                shutil.rmtree(path)
                self.report.cleaned_caches += 1
                logger.debug(f"Deleted cache dir: {path}")
            except OSError as e:
                logger.warning(f"Could not remove {path}: {e}")

        # Strategy: Cleanup orphaned .pyc files
        for path in self.root.rglob("*.pyc"):
            if "venv" in path.parts: continue
            try:
                path.unlink()
                self.report.cleaned_caches += 1
            except OSError:
                pass
        
        logger.info(f"✨ Purge complete. Removed {self.report.cleaned_caches} cache artifacts.")

    def _check_git_conflicts(self, filepath: Path, content: str) -> None:
        """Scans for raw git merge conflict markers."""
        if "<<<<<<< HEAD" in content:
            # Find the line number manually since AST fails on this
            lines = content.splitlines()
            for idx, line in enumerate(lines, 1):
                if "<<<<<<< HEAD" in line:
                    self.report.conflicts_found.append(
                        ScanResult(filepath, "GIT_CONFLICT", idx, "Unresolved merge conflict detected")
                    )

    def _validate_syntax(self, filepath: Path, content: str) -> None:
        """Uses Python's AST to validate syntax without executing."""
        try:
            ast.parse(content)
        except SyntaxError as e:
            self.report.syntax_errors.append(
                ScanResult(filepath, "SYNTAX_ERROR", e.lineno or 0, str(e.msg))
            )
        except Exception as e:
            self.report.syntax_errors.append(
                ScanResult(filepath, "PARSING_ERROR", 0, str(e))
            )

    @measure_performance
    def scan_integrity(self) -> None:
        """
        Performs static analysis on all Python files to find merge conflicts
        or syntax errors that might be invisible to the runtime until called.
        """
        logger.info("🔍 Starting Integrity Scan (AST Analysis)...")
        
        for file_path in self._python_files:
            try:
                # Read with 'replace' errors to avoid crashing on encoding mess
                content = file_path.read_text(encoding='utf-8', errors='replace')
                
                # Check 1: Git Conflicts
                self._check_git_conflicts(file_path, content)
                
                # Check 2: Syntax Validity
                self._validate_syntax(file_path, content)

            except Exception as e:
                logger.error(f"Failed to analyze file {file_path}: {e}")

    def produce_verdict(self) -> None:
        """Outputs the final judgment."""
        print("\n" + "="*60)
        print(f"🕵️  ARCHITECT'S DIAGNOSIS REPORT FOR: {self.root.name}")
        print("="*60)
        
        if self.report.is_healthy:
            print(f"\n✅ STATUS: HEALTHY")
            print(f"   - Caches purged: {self.report.cleaned_caches}")
            print(f"   - No syntax errors or merge conflicts found.")
            print("\n👉 Recommendation: Try running your app now. The ghosts are gone.")
        else:
            print(f"\n❌ STATUS: CRITICAL ISSUES DETECTED")
            
            if self.report.conflicts_found:
                print(f"\n[!] MERGE CONFLICTS (The 'git pull' killer):")
                for conflict in self.report.conflicts_found:
                    print(f"    -> {conflict.filepath}:{conflict.line_number} | {conflict.details}")
            
            if self.report.syntax_errors:
                print(f"\n[!] SYNTAX ERRORS (Code that cannot compile):")
                for err in self.report.syntax_errors:
                    print(f"    -> {err.filepath}:{err.line_number} | {err.details}")
            
            print("\n👉 Action Required: Fix these files manually before running anything.")
        print("="*60 + "\n")

# --- Execution Entry Point ---
def main():
    # Use context manager for safe path handling
    try:
        with ProjectScopeManager(".") as root_path:
            sanitizer = ProjectSanitizer(root_path)
            
            # Step 1: Clean the environment
            sanitizer.purge_bytecode()
            
            # Step 2: Verify code integrity
            sanitizer.scan_integrity()
            
            # Step 3: Report
            sanitizer.produce_verdict()
            
    except KeyboardInterrupt:
        print("\n⚠️  Aborted by user.")
    except Exception as e:
        logger.critical(f"Unexpected architectural failure: {e}", exc_info=True)

if __name__ == "__main__":
    main()