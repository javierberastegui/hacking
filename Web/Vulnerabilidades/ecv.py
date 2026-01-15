import asyncio
import nmap
import os
import re
from typing import Final, AsyncIterator, Optional
from dataclasses import dataclass
from urllib.parse import urlparse
from getpass import getpass

from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from pymetasploit3.msfrpc import MsfRpcClient

console = Console()

@dataclass(frozen=True)
class ServiceFound:
    port: int
    product: str
    version: str

class StealthEngine:
    def __init__(self, target: str, use_tor: bool = False):
        # Saneamiento extremo
        target = target.strip().replace("https://", "").replace("http://", "")
        self._target = target.split("/")[0].split(":")[0]
        self._nm = nmap.PortScanner()
        self._use_tor = use_tor

    async def scan(self) -> AsyncIterator[ServiceFound]:
        loop = asyncio.get_running_loop()
        
        # Arsenal Stealth: Fragmentación (-f) y MTU bajo para bypass WAF
        # Bajamos timing a T2 para ser indetectables
        evasion_args = "-sV -Pn -T2 -f --mtu 8 --data-length 32 --open"
        
        if self._use_tor:
            # Requiere 'sudo apt install tor' y 'sudo service tor start'
            evasion_args += " --proxies http://127.0.0.1:9050"
            console.log("[bold magenta]🛡️  Bypass Activo:[/bold magenta] Enrutando ráfagas por Tor...")

        try:
            console.log(f"[yellow][⚡][/yellow] Iniciando ráfagas fragmentadas hacia [bold]{self._target}[/bold]...")
            await loop.run_in_executor(None, lambda: self._nm.scan(self._target, arguments=evasion_args))
        except Exception as e:
            console.log(f"[bold red]✘ Error en Nmap:[/bold red] {str(e).splitlines()[0]}")
            if "privileges" in str(e):
                console.log("[yellow]Tip:[/yellow] Ejecuta: 'sudo setcap cap_net_raw,cap_net_admin,cap_net_bind_service+eip $(which nmap)'")
            return

        for host in self._nm.all_hosts():
            for proto in self._nm[host].all_protocols():
                for port in sorted(self._nm[host][proto].keys()):
                    svc = self._nm[host][proto][port]
                    yield ServiceFound(port, svc.get('product', 'Desconocido'), svc.get('version', 'N/A'))

class CyberSentinel:
    def __init__(self, target: str):
        self.target = target
        self.table = Table(title=f"Evasión Avanzada: {target}", expand=True, border_style="blue")
        self.table.add_column("PORT", style="cyan", width=12)
        self.table.add_column("SERVICE/VERSION", style="white")
        self.table.add_column("MSF INTEL", justify="right")

    async def execute(self):
        console.print("[bold yellow]🔑 Acceso a la Estación de Combate[/bold yellow]")
        msf_pass = getpass("➤ Clave MSFRPC: ")
        
        try:
            # Conexión con SSL para evitar 'Connection reset'
            msf = MsfRpcClient(msf_pass, port=55553, host="127.0.0.1", ssl=True)
            console.log("[bold green]✔[/bold green] Sincronizado con Metasploit Framework.")
        except Exception as e:
            console.log(f"[bold red]✘ Fallo de enlace MSF:[/bold red] {e}")
            return

        engine = StealthEngine(self.target, use_tor=False)
        
        with Live(Panel(self.table, title="[bold red]SENTINEL ACTIVE[/bold red]", subtitle="Bypassing WAF with fragmented packets"), console=console) as live:
            async for service in engine.scan():
                query = f"{service.product} {service.version}"
                res = msf.modules.search(query)
                
                status = f"[bold red]VULNERABLE ({len(res)})[/bold red]" if res else "[dim]Filtrado/Seguro[/dim]"
                self.table.add_row(f"TCP/{service.port}", f"{service.product} [dim]{service.version}[/dim]", status)
                live.update(Panel(self.table))

async def main():
    console.print(Panel.fit("[bold blue]HP OMEN - STEALTH SECURITY ORCHESTRATOR[/bold blue]\n[dim]v8.0 | Zero-Trace Edition[/dim]"))
    target = console.input("[bold white]➤ Objetivo (IP/Dominio): [/bold white]")
    if not target: return
    
    sentinel = CyberSentinel(target)
    await sentinel.execute()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[bold red]✘ Abortando operación...[/bold red]")