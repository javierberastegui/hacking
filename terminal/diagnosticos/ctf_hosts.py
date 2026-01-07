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
        # We handle exceptions if needed, but returning None propagates them (desired behavior)

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
                    return # Nothing added, nothing to track

        if not found:
            # Check if hostname exists on another IP (conflict resolution could go here)
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
        # Reload fresh to avoid race conditions (paranoia mode)
        self._load_entries()
        
        modified = False
        for ip, hostname in self.session_created:
            for entry in self.entries:
                if not entry.is_comment and entry.ip_address == ip:
                    if hostname in entry.hostnames:
                        entry.hostnames.remove(hostname)
                        print(f"🗑️  Revoked: {hostname} from {ip}")
                        modified = True
                    
                    # If entry has no more hostnames, mark for deletion (optional, but clean)
                    if not entry.hostnames:
                         # We'll filter empty entries during write or simple filter here
                         pass 

        # Filter out entries that lost all hostnames (ghost IPs)
        self.entries = [e for e in self.entries if e.is_comment or len(e.hostnames) > 0]
        
        if modified:
            self._flush()

# --- Interactive Loop ---

def get_input(prompt: str) -> str:
    """Helper for clean input handling."""
    try:
        return input(prompt).strip()
    except EOFError:
        return "exit"

@require_root
def main_loop() -> None:
    print("💀 CTF Hosts Manager - Ephemeral Mode")
    print("-------------------------------------")
    print("• Enter 'exit', 'quit' or Ctrl+C to finish.")
    print("• Format: IP HOSTNAME (e.g., 10.10.10.55 machine.htb)")
    print("-------------------------------------\n")

    # The Context Manager handles the lifecycle
    with EphemeralHostsSession() as session:
        while True:
            try:
                user_input = get_input("root@hosts-injector:~# ")
                
                if user_input.lower() in ["exit", "quit"]:
                    break
                
                if not user_input:
                    continue

                parts = user_input.split()
                if len(parts) < 2:
                    print("⚠️  Invalid format. Need: <IP> <HOSTNAME> [ALIAS...]")
                    continue

                ip = parts[0]
                hostnames = parts[1:]

                # Basic validation (could be regex, but let's trust the user a bit)
                for host in hostnames:
                    session.add_target(ip, host)

            except KeyboardInterrupt:
                print("\n\n⚠️  Interrupted! Initiating emergency cleanup...")
                break
            except Exception as e:
                print(f"💥 Unexpected error: {e}")
                break

if __name__ == "__main__":
    main_loop()