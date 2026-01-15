import re
import pdfplumber
import pandas as pd
from typing import List, Dict, Pattern
from dataclasses import dataclass, asdict
from pathlib import Path
import sys

# --- DOMAIN LAYER ---
@dataclass
class Transaction:
    operation_date: str
    code: str
    concept: str
    value_date: str
    amount: float

class StatementParser:
    """
    Motor de extracción v3.0 - Especializado en PDFs con saltos de línea irregulares.
    """
    
    # EXPLICACIÓN TÉCNICA:
    # Usamos re.DOTALL | re.MULTILINE para que el punto (.) pille saltos de línea.
    # \s* se come cualquier espacio o salto de línea entre las comas y las comillas.
    # Esto arregla el problema de que tu PDF ponga la fecha en una línea y el importe en otra.
    _TRANSACTION_PATTERN: Pattern = re.compile(
        r'"(\d{4}-\d{2}-\d{2})"\s*,\s*"(\d+)"\s*,\s*"(.*?)"\s*,\s*"(\d{4}-\d{2}-\d{2})"\s*,\s*"([\d\.,]+)\s*"?',
        re.DOTALL
    )

    def __init__(self, file_path: Path):
        self.file_path = file_path

    def _clean_amount(self, raw_amount: str) -> float:
        # Limpiamos puntos de miles y cambiamos coma decimal por punto
        clean = raw_amount.replace('.', '').replace(',', '.')
        try:
            return float(clean)
        except ValueError:
            return 0.0

    def parse(self) -> pd.DataFrame:
        transactions: List[Dict] = []
        try:
            with pdfplumber.open(self.file_path) as pdf:
                print(f"⚙️  Escaneando {len(pdf.pages)} páginas (Modo Deep Scan)...")
                
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if not text: continue
                    
                    # Buscamos en todo el texto de la página a la vez, no línea a línea
                    matches = self._TRANSACTION_PATTERN.finditer(text)
                    
                    for match in matches:
                        # Limpiamos los saltos de línea que pueda haber DENTRO del concepto
                        concept_clean = match.group(3).replace('\n', ' ').replace('\r', '').strip()
                        # Quitamos espacios dobles generados
                        concept_clean = re.sub(r'\s+', ' ', concept_clean)

                        trans = Transaction(
                            operation_date=match.group(1),
                            code=match.group(2),
                            concept=concept_clean,
                            value_date=match.group(4),
                            amount=self._clean_amount(match.group(5))
                        )
                        transactions.append(asdict(trans))
                        
            return pd.DataFrame(transactions)
            
        except Exception as e:
            print(f"🔥 Error crítico leyendo el PDF: {e}")
            sys.exit(1)

# --- PRESENTATION LAYER ---

def get_source_path() -> Path:
    while True:
        raw_input = input("\n📂 Arrastra el archivo 'EXTRACTO TPV.pdf' aquí: ").strip()
        
        # Limpieza agresiva de comillas que mete Linux al arrastrar
        if len(raw_input) > 1 and raw_input[0] in ['"', "'"] and raw_input[-1] == raw_input[0]:
            raw_input = raw_input[1:-1]

        path = Path(raw_input)
        
        if path.exists() and path.is_file():
            return path.resolve()
        
        print(f"❌ No encuentro el archivo. Asegúrate de arrastrar el PDF correcto.")

def main():
    print("\n--- 🚀 EXTRACTOR TPV v3.0 (Versión Blindada) ---\n")
    
    # 1. Input
    source_file = get_source_path()
    
    # 2. Path Calculation
    output_file = source_file.with_suffix('.xlsx')
    print(f"📍 Guardaré el Excel en: {output_file.name}")

    # 3. Process
    parser = StatementParser(source_file)
    df = parser.parse()

    # 4. Output
    if not df.empty:
        # Ordenamos por fecha
        df = df.sort_values(by='operation_date', ascending=False)
        try:
            df.to_excel(output_file, index=False)
            print(f"\n✅ ¡FUNCIONÓ! {len(df)} movimientos extraídos.")
            print(f"📂 Tu archivo está aquí: {output_file}")
        except PermissionError:
            print(f"\n⛔ CIERRA EL EXCEL. No puedo escribir si lo tienes abierto.")
    else:
        print("\n⚠️  Sigo sin ver datos. Esto es rarísimo. ¿Seguro que es el PDF correcto?")

if __name__ == "__main__":
    main()