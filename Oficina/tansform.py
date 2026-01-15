import re
import pdfplumber
import pandas as pd
from typing import List, Dict
from dataclasses import dataclass, asdict
from pathlib import Path
import sys

# --- ESTRUCTURA DE DATOS ---
@dataclass
class Transaction:
    operation_date: str
    code: str
    concept: str
    value_date: str
    amount: float

class StatementParser:
    """
    Motor v5.0: "The Tokenizer"
    Estrategia: Cortar el texto por comillas (") y buscar secuencias lógicas de datos.
    Ignora totalmente el formato visual, solo le importan los datos puros.
    """

    def __init__(self, file_path: Path):
        self.file_path = file_path

    def _is_date(self, text: str) -> bool:
        # Verifica si parece una fecha YYYY-MM-DD
        return bool(re.match(r'^\s*\d{4}-\d{2}-\d{2}\s*$', text))

    def _clean_amount(self, raw_amount: str) -> float:
        # Limpia 1.000,00 -> 1000.00
        clean = raw_amount.strip().replace('.', '').replace(',', '.')
        try:
            return float(clean)
        except ValueError:
            return 0.0

    def parse(self) -> pd.DataFrame:
        transactions: List[Dict] = []
        full_text_blob = ""

        try:
            with pdfplumber.open(self.file_path) as pdf:
                print(f"⚙️  Triturando {len(pdf.pages)} páginas...")
                # 1. Unimos TODO el PDF en una sola masa de texto gigante
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        full_text_blob += text + "\n"

            # 2. LA MAGIA: Dividimos por comillas dobles (")
            # Esto nos da una lista: [basura, FECHA, basura, CODIGO, basura, CONCEPTO...]
            tokens = full_text_blob.split('"')
            
            # Limpiamos tokens vacíos o que sean solo comas/espacios
            tokens = [t.strip() for t in tokens]
            
            print(f"📊 Analizando {len(tokens)} fragmentos de datos...")

            # 3. Buscamos patrones en la lista de fragmentos
            i = 0
            while i < len(tokens) - 8:
                # Buscamos una fecha para empezar (Campo 1: F. Operación)
                if self._is_date(tokens[i]):
                    
                    # HIPÓTESIS: Si tokens[i] es fecha, los siguientes deberían ser:
                    # i+0: Fecha Oper
                    # i+1: separador (comas, saltos, basura) -> LO SALTAMOS
                    # i+2: Código
                    # i+3: separador
                    # i+4: Concepto
                    # i+5: separador
                    # i+6: Fecha Valor
                    # i+7: separador
                    # i+8: Importe
                    
                    # Verificamos si token[i+6] también es fecha para confirmar que es una fila válida
                    # A veces los separadores son tokens vacíos en la lista, así que miramos un rango corto
                    
                    # Búsqueda local de los siguientes campos
                    # Cogemos los siguientes 10 tokens y filtramos los que no sean separadores (comas)
                    candidates = []
                    offset = 0
                    while len(candidates) < 5 and (i + offset) < len(tokens):
                        val = tokens[i + offset]
                        # Si es un valor "útil" (no es solo una coma o vacío)
                        if len(val) > 1 or val.isalnum(): 
                            candidates.append(val)
                        offset += 1
                    
                    if len(candidates) == 5:
                        # Validamos estructura fuerte: Fecha1 y Fecha2
                        op_date, code, concept, val_date, amount_str = candidates
                        
                        if self._is_date(op_date) and self._is_date(val_date):
                            # ¡BINGO! Hemos encontrado una fila
                            trans = Transaction(
                                operation_date=op_date.strip(),
                                code=code.strip(),
                                concept=concept.strip().replace('\n', ' '),
                                value_date=val_date.strip(),
                                amount=self._clean_amount(amount_str)
                            )
                            transactions.append(asdict(trans))
                            # Saltamos el índice para no volver a procesar estos tokens
                            i += offset - 1 
                
                i += 1

            return pd.DataFrame(transactions)

        except Exception as e:
            print(f"🔥 Error crítico: {e}")
            sys.exit(1)

# --- INTERFAZ ---

def get_source_path() -> Path:
    while True:
        raw_input = input("\n📂 Arrastra el PDF aquí: ").strip()
        if len(raw_input) > 1 and raw_input[0] in ['"', "'"] and raw_input[-1] == raw_input[0]:
            raw_input = raw_input[1:-1]
        path = Path(raw_input)
        if path.exists() and path.is_file(): return path.resolve()
        print(f"❌ Archivo no encontrado.")

def main():
    print("\n--- 🚀 EXTRACTOR TPV v5.0 (Modo Trituradora) ---\n")
    source_file = get_source_path()
    output_file = source_file.with_suffix('.xlsx')
    
    parser = StatementParser(source_file)
    df = parser.parse()

    if not df.empty:
        df = df.sort_values(by='operation_date', ascending=False)
        # Reordenar columnas para que quede bonito
        df = df[['operation_date', 'code', 'concept', 'value_date', 'amount']]
        df.to_excel(output_file, index=False)
        print(f"\n✅ ¡CONSEGUIDO! {len(df)} movimientos recuperados.")
        print(f"💾 Guardado en: {output_file}")
    else:
        print("\n⚠️  Sigo sin datos. Esto ya es personal. Pásame una captura de este error.")

if __name__ == "__main__":
    main()