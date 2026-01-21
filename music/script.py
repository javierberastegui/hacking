import logging
import sys
from dataclasses import dataclass
from typing import Protocol, Optional
from pathlib import Path
from yt_dlp import YoutubeDL

# --- CONFIG & TYPES ---

@dataclass(frozen=True)
class SongMetadata:
    url: str
    download_path: Path = Path("./downloads")

class DownloaderEngine(Protocol):
    def download(self, metadata: SongMetadata) -> bool:
        ...

# --- CORE LOGIC ---

class YoutubeAudioEngine:
    """Motor robusto configurado para MP3 192kbps e ignorando playlists."""
    
    def __init__(self):
        self._opts = {
            'format': 'bestaudio/best',
            'outtmpl': '%(title)s.%(ext)s',
            # ESTA ES LA CLAVE: Le decimos que pase de las listas olímpicamente
            'noplaylist': True, 
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
            'no_warnings': True,
        }

    def download(self, metadata: SongMetadata) -> bool:
        current_opts = self._opts.copy()
        current_opts['outtmpl'] = f"{metadata.download_path}/%(title)s.%(ext)s"
        
        try:
            with YoutubeDL(current_opts) as ydl:
                # El download=True aquí hace el trabajo sucio
                info = ydl.extract_info(metadata.url, download=True)
                
                # Gestión de errores si info viene vacío (raro, pero posible)
                if not info:
                    return False

                # Si por casualidad yt-dlp devuelve una lista (entries), cogemos el primero
                if 'entries' in info:
                    info = info['entries'][0]

                title = info.get('title', 'Unknown')
                logging.info(f"✅ Descarga completada: {title}")
                return True
        except Exception as e:
            # Limpiamos el error para que no ensucie la terminal visualmente
            error_msg = str(e).split(';')[0] 
            logging.info(f"❌ Error: {error_msg}")
            return False

class InteractiveSession:
    """Clase para manejar el bucle de interacción con el usuario."""
    
    def __init__(self, engine: DownloaderEngine):
        self.engine = engine
        self.download_dir = Path("mis_canciones")
        self._setup_storage()

    def _setup_storage(self) -> None:
        if not self.download_dir.exists():
            self.download_dir.mkdir(parents=True)
            logging.info(f"📁 Carpeta destino: {self.download_dir.absolute()}")

    def start(self):
        print("\n" + "="*45)
        print(" 🎵 YOUTUBE SINGLE TRACK DOWNLOADER")
        print("    (Modo Anti-Playlist Activado)")
        print("    Pega la URL y dale caña.")
        print("="*45 + "\n")

        while True:
            try:
                user_input = input(">> Introduce URL: ").strip()

                if user_input.lower() in ('exit', 'q', 'salir'):
                    print("\n👋 Ciao.")
                    break
                
                if not user_input:
                    continue

                print("⏳ Procesando...", end='\r')
                self.engine.download(SongMetadata(url=user_input, download_path=self.download_dir))
                
            except KeyboardInterrupt:
                print("\n\n🛑 Saliendo a la fuerza.")
                sys.exit(0)

# --- EXECUTION ---

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    engine = YoutubeAudioEngine()
    app = InteractiveSession(engine)
    app.start()