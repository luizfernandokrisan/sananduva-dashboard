"""Configurações centrais do dashboard Sananduva."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
EXCEL_PATH = DATA_DIR / "Base_DB_Sananduva.xlsx"
SQLITE_PATH = DATA_DIR / "sananduva.db"

PLANILHAS = ["Abate", "Condenas", "Producao"]

# Schema esperado por planilha (validação)
SCHEMA = {
    "Abate":    ["Data", "Parceiro", "Tipo_Suino", "Quantidade", "Peso_Vivo_Kg", "Peso_Carcaca_Quente_Kg"],
    "Condenas": ["Data", "Parceiro", "Tipo_Condena", "Peso_Condena"],
    "Producao": ["Data", "Parceiro", "SKU", "Nome_Produto", "Família", "Total_Produzido"],
}

# Paleta inspirada na referência ECOFRIGO (verdes + neutros)
CORES = {
    "primaria":   "#1B5E20",
    "secundaria": "#2E7D32",
    "clara":      "#A5D6A7",
    "destaque":   "#FFC107",
    "alerta":     "#C62828",
    "fundo":      "#F5F7F5",
    "card":       "#FFFFFF",
    "texto":      "#212121",
    "texto_fraco":"#757575",
}

PARCEIROS = ["BRF", "ECOFRIGO", "JBS", "PAMPLONA"]
