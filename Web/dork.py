import cloudscraper
from lxml import etree
import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

class SitemapHeist:
    def __init__(self, domain):
        if not domain.startswith("http"):
            domain = f"https://{domain}"
        self.base_url = domain.rstrip("/")
        # Instanciamos el scraper que salta Cloudflare
        self.scraper = cloudscraper.create_scraper()

    def run(self):
        console.print(Panel(f"[bold red]🏴‍☠️ INICIANDO ROBO DE SITEMAP: {self.base_url}[/]", border_style="red"))
        
        # Lista de objetivos probables (Sitemaps estándar de WordPress/Yoast)
        targets = [
            "/page-sitemap.xml",  # El que tú viste
            "/post-sitemap.xml",  # Artículos de blog
            "/sitemap_index.xml", # Índice general
            "/sitemap.xml",       # Estándar
            "/wp-sitemap.xml"     # WordPress 5.5+
        ]

        found_total = set()

        for path in targets:
            full_target = self.base_url + path
            console.print(f"[dim]⚡ Intentando asalto a: {full_target}...[/]")
            
            try:
                # 1. Petición con Cloudscraper (Bypass WAF)
                resp = self.scraper.get(full_target)
                
                if resp.status_code == 200 and ("xml" in resp.headers.get('Content-Type', '') or b'urlset' in resp.content):
                    console.print(f"[green]🔓 ¡ACCESO CONCEDIDO! Descargando...[/]")
                    urls = self._parse_xml(resp.content)
                    if urls:
                        console.print(f"   └── [bold white]Robadas {len(urls)} URLs de este mapa.[/]")
                        found_total.update(urls)
                else:
                    console.print(f"   [yellow]⛔ Fallo o vacío (Status {resp.status_code})[/]")

            except Exception as e:
                console.print(f"   [red]💥 Error de conexión: {e}[/]")

        self._print_loot(found_total)

    def _parse_xml(self, content):
        """Extrae URLs limpias del XML ignorando namespaces"""
        extracted = []
        try:
            # Usamos lxml para parsear, es más robusto
            root = etree.fromstring(content)
            # Buscamos cualquier tag que se llame 'loc' (location) sin importar el namespace
            for url in root.xpath('//*[local-name()="loc"]'):
                if url.text:
                    extracted.append(url.text)
        except Exception as e:
            console.print(f"[red]Error parseando XML: {e}[/]")
        return extracted

    def _print_loot(self, urls):
        console.print("\n")
        if not urls:
            console.print("[bold red]💀 No se pudo robar nada. El WAF es muy duro o los sitemaps no existen.[/]")
            return

        table = Table(title=f"💰 BOTÍN COMPLETO ({len(urls)} URLs)", show_lines=True)
        table.add_column("ID", style="dim", width=4)
        table.add_column("URL Objetivo", style="green bold")

        for idx, url in enumerate(sorted(urls), 1):
            table.add_row(str(idx), url)

        console.print(table)

if __name__ == "__main__":
    target = "javierberastegui.es"
    if len(sys.argv) > 1:
        target = sys.argv[1]
    
    heist = SitemapHeist(target)
    heist.run()