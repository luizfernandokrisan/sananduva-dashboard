"""Camada de acesso a dados: hoje Excel, amanhã Oracle.
A interface DataLoader.load() é a ÚNICA que o resto do dashboard conhece."""
from __future__ import annotations
import sqlite3
import pandas as pd
from pathlib import Path
from config import EXCEL_PATH, SQLITE_PATH, PLANILHAS, SCHEMA


def _normaliza_datas(serie: pd.Series) -> pd.Series:
    """Excel salvou datas em dois formatos:
       - datetime (quando dia <= 12 → ambiguidade resolvida pelo Excel)
       - string  'dd/mm/aaaa' (quando dia > 12)
       Aqui forçamos UM tipo único: pd.Timestamp."""
    return pd.to_datetime(serie, dayfirst=True, errors="coerce")


def _valida_schema(df: pd.DataFrame, nome: str) -> None:
    esperado = SCHEMA[nome]
    faltando = set(esperado) - set(df.columns)
    if faltando:
        raise ValueError(f"[{nome}] colunas ausentes: {faltando}")


class DataLoader:
    """Hoje: source='excel'. Amanhã: 'sqlite' ou 'oracle' sem mudar o dashboard."""

    def __init__(self, source: str = "excel", path: Path | None = None):
        self.source = source
        self.path = path or (EXCEL_PATH if source == "excel" else SQLITE_PATH)

    # API pública -----------------------------------------------------
    def load(self) -> dict[str, pd.DataFrame]:
        dfs = getattr(self, f"_from_{self.source}")()
        for nome, df in dfs.items():
            _valida_schema(df, nome)
            df["Data"] = _normaliza_datas(df["Data"])
            df.dropna(subset=["Data"], inplace=True)
        return dfs

    # Fontes ----------------------------------------------------------
    def _from_excel(self) -> dict[str, pd.DataFrame]:
        return pd.read_excel(self.path, sheet_name=PLANILHAS)

    def _from_sqlite(self) -> dict[str, pd.DataFrame]:
        with sqlite3.connect(self.path) as con:
            return {t: pd.read_sql(f"SELECT * FROM {t}", con) for t in PLANILHAS}

    def _from_oracle(self) -> dict[str, pd.DataFrame]:
        # Plug futuro: oracledb + SQLAlchemy. Mesmo dict de saída.
        raise NotImplementedError("Conexão Oracle a implementar na Fase 4.")


if __name__ == "__main__":
    dfs = DataLoader().load()
    for n, df in dfs.items():
        print(f"{n:10s} {df.shape}  período: {df['Data'].min().date()} → {df['Data'].max().date()}")
