"""Ponte Excel → SQLite. Roda uma vez para 'congelar' a base num DB consultável.
   Quando migrar para Oracle, este arquivo vira oracle_bridge.py — mesma lógica."""
import sqlite3
import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from config import SQLITE_PATH, EXCEL_PATH
from data_loader import DataLoader

SCHEMA_SQL = Path(__file__).with_name("schema.sql").read_text()


def migrar_excel_para_sqlite(db_path: Path = SQLITE_PATH) -> None:
    dfs = DataLoader(source="excel", path=EXCEL_PATH).load()

    # Producao: 'Família' (com acento) → 'Familia' no SQL
    dfs["Producao"] = dfs["Producao"].rename(columns={"Família": "Familia"})

    with sqlite3.connect(db_path) as con:
        con.executescript(SCHEMA_SQL)
        for tabela, df in dfs.items():
            df.to_sql(tabela, con, if_exists="append", index=False)
            print(f"  ✓ {tabela}: {len(df)} linhas inseridas")

    print(f"\n✓ Banco criado em: {db_path}")


if __name__ == "__main__":
    migrar_excel_para_sqlite()
