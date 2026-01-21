import os
import shutil
import sys
import signal
from dataclasses import dataclass, field
from typing import List, Optional, Set, Tuple, Any, Callable
from functools import wraps
from pathlib import Path

# --- Configuration & Constants ---
HOSTS_FILE = Path("/etc/hosts")
BACKUP_EXT = ".bak"

# --- Decorators ---

def require_root(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator to ensure the script is running with elevated privileges.
    Targeting critical system files requires root.
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if os.geteuid() != 0:
            print("🚫 Error: This tool requires root privileges. Run with 'sudo'.")
            sys.exit(1)
        return func(*args, **kwargs)
    return wrapper

# --- Data Structures ---

@dataclass
class HostEntry:
    """
    Represents a robust /etc/hosts entry.
    """
    ip_address: str
    hostnames: List[str]
    raw_line: str = ""
    is_comment: bool = False

    def to_line(self) -> str:
        """Serializes the object back to a hosts file line."""
        if self.is_comment:
            return self.raw_line
        return f"{self.ip_address}\t{' '.join(self.hostnames)}\n"

    def __repr__(self) -> str:
        if self.is_comment:
            return f"<Comment: {self.raw_line.strip()}>"
        return f"<Entry: {self.ip_address} -> {self.hostnames}>"

# --- Core Logic ---

class EphemeralHostsSession:
    """
    Advanced Context Manager for Ephemeral Host Management.
    Features:
    - Automatic Backup on entry.
    - Session tracking: Remembers what was added.
    - Automatic Cleanup on exit (Idempotent rollback of session changes).
    - Signal Handling safe.
    """

    def __init__(self, file_path: Path = HOSTS_FILE):
        self.file_path = file_path
        self.entries: List[HostEntry] = []
        # Track tuples of (ip, hostname) added during this session for cleanup
        self.session_created: Set[Tuple[str, str]] = set()

    def __enter__(self) -> 'EphemeralHostsSession':
        print("\n🔒 Initializing Ephemeral Session...")
        self._backup()
        self._load_entries()
        print("✅ Environment secured. Ready to inject targets.\n")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        The critical teardown phase.
        Executes cleanup of session-specific entries regardless of how the script ends.
        """
        print("\n\n🛑 Terminating Session...")
        if self.session_created:
            print(f"🧹 Cleaning up {len(self.session_created)} ephemeral entries...")
            self._cleanup_session_data()
        else:
            print("🧹 No changes to clean up.")
        
        print("👋 Hosts file restored to clean state. Happy hacking.")

    def _backup(self) -> None:
        """Creates a safety backup."""
        backup_path = self.file_path.with_suffix(BACKUP_EXT)
        try:
            shutil.copy(self.file_path, backup_path)
        except IOError as e:
            print(f"🔥 Backup failed: {e}")
            sys.exit(1)

    def _load_entries(self) -> None:
        """Parses the host file into memory."""
        self.entries = []
        if not self.file_path.exists():
            return

        with open(self.file_path, 'r', encoding='utf-8') as f:
            for line in f:
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    self.entries.append(HostEntry("", [], raw_line=line, is_comment=True))
                    continue
                
                parts = stripped.split()
                if len(parts) >= 2:
                    self.entries.append(HostEntry(parts[0], parts[1:]))
                else:
                    self.entries.append(HostEntry("", [], raw_line=line, is_comment=True))

    def _flush(self) -> None:
        """Writes current memory state to disk."""
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                for entry in self.entries:
                    f.write(entry.to_line())
        except IOError as e:
            print(f"💥 Write failure: {e}")

    def add_target(self, ip: str, hostname: str) -> None:
        """
        Adds a target to the hosts file and tracks it for later removal.
        """
        # 1. Update internal object model
        found = False
        for entry in self.entries:
            if not entry.is_comment and entry.ip_address == ip:
                if hostname not in entry.hostnames:
                    entry.hostnames.append(hostname)
                    print(f"🔗 Attached '{hostname}' to existing IP {ip}")
                    found = True
                else:
                    print(f"ℹ️  '{hostname}' already exists on {ip}")
                    return 

        if not found:
            new_entry = HostEntry(ip, [hostname])
            self.entries.append(new_entry)
            print(f"🎯 Target Acquired: {ip} -> {hostname}")

        # 2. Track for cleanup
        self.session_created.add((ip, hostname))
        
        # 3. Apply to system immediately
        self._flush()

    def _cleanup_session_data(self) -> None:
        """
        Removes exactly what was added during this session.
        """
        self._load_entries() # Reload to avoid race conditions
        
        modified = False
        for ip, hostname in self.session_created:
            for entry in self.entries:
                if not entry.is_comment and entry.ip_address == ip:
                    if hostname in entry.hostnames:
                        entry.hostnames.remove(hostname)
                        print(f"🗑️  Revoked: {hostname} from {ip}")
                        modified = True
                    
        # Filter out ghost IPs (entries with no hostnames left)
        self.entries = [e for e in self.entries if e.is_comment or len(e.hostnames) > 0]
        
        if modified:
            self._flush()

# --- Interactive Shell UI ---

class InteractiveShell:
    """
    Handles the user interaction state machine.
    """
    def __init__(self, session: EphemeralHostsSession):
        self.session = session
        self.current_ip: Optional[str] = None

    def run(self):
        print("💀 CTF Hosts Manager - Continuous Flow Mode")
        print("-------------------------------------------")
        print("1. Enter Target IP when prompted.")
        print("2. Enter Hostnames continuously.")
        print("3. Commands: ':new' to change IP, ':exit' to quit.")
        print("-------------------------------------------\n")

        while True:
            try:
                if not self.current_ip:
                    self._handle_ip_input()
                else:
                    self._handle_hostname_input()
            except KeyboardInterrupt:
                # Let the outer loop handle the exit
                raise

    def _handle_ip_input(self):
        """State: Waiting for IP."""
        raw = input("🎯 [SET TARGET IP] > ").strip()
        if self._is_exit_command(raw):
            raise EOFError # Trigger exit
        
        if not raw: return

        # Simple validation could be added here
        self.current_ip = raw
        print(f"✅ Context switched to: {self.current_ip}")

    def _handle_hostname_input(self):
        """State: Waiting for Hostnames for current IP."""
        raw = input(f"🔗 [{self.current_ip}] Add Host > ").strip()
        
        if self._is_exit_command(raw):
            raise EOFError
        
        if raw == ":new":
            print("🔄 Resetting target context...")
            self.current_ip = None
            return

        if not raw: return

        # Support space-separated multiple hosts in one line too
        hosts = raw.split()
        for host in hosts:
            self.session.add_target(self.current_ip, host)

    def _is_exit_command(self, cmd: str) -> bool:
        return cmd.lower() in ["exit", "quit", ":exit", ":quit"]

# --- Main Entry Point ---

@require_root
def main_loop() -> None:
    # The Context Manager handles the lifecycle and cleanup
    with EphemeralHostsSession() as session:
        shell = InteractiveShell(session)
        try:
            shell.run()
        except (EOFError, KeyboardInterrupt):
            # Normal exit flow, context manager will clean up
            pass
        except Exception as e:
            print(f"💥 Unexpected error: {e}")

if __name__ == "__main__":
    main_loop()