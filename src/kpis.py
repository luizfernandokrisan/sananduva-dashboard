"""KPIs de alto nível — alimentam os cards do dashboard (visão diretoria)."""
import pandas as pd


def kpis_executivos(fato: pd.DataFrame) -> dict:
    """Resume o fato consolidado em 6 indicadores principais."""
    if fato.empty:
        return {}

    pv  = fato["Peso_Vivo_Kg"].sum()
    pcq = fato["Peso_Carcaca_Kg"].sum()
    pc  = fato["Peso_Condena_Kg"].sum()
    pp  = fato["Total_Produzido_Kg"].sum()
    cab = fato["Cabecas"].sum()

    return {
        "cabecas_abatidas":      int(cab),
        "peso_vivo_total_kg":    float(pv),
        "peso_carcaca_total_kg": float(pcq),
        "peso_produzido_kg":     float(pp),
        "rend_carcaca_pct":      (pcq / pv * 100) if pv else 0.0,
        "rend_industrial_pct":   (pp / pv * 100) if pv else 0.0,
        "taxa_condena_pct":      (pc / pv * 100) if pv else 0.0,
        "peso_medio_kg":         (pv / cab)      if cab else 0.0,
    }


def kpis_por_parceiro(fato: pd.DataFrame) -> pd.DataFrame:
    """Ranking por parceiro — quem é o mais eficiente?"""
    g = (fato.groupby("Parceiro", as_index=False)
              .agg(Cabecas=("Cabecas", "sum"),
                   Peso_Vivo_Kg=("Peso_Vivo_Kg", "sum"),
                   Peso_Carcaca_Kg=("Peso_Carcaca_Kg", "sum"),
                   Peso_Condena_Kg=("Peso_Condena_Kg", "sum"),
                   Produzido_Kg=("Total_Produzido_Kg", "sum")))
    g["Rend_Carcaca_%"]    = g["Peso_Carcaca_Kg"]  / g["Peso_Vivo_Kg"] * 100
    g["Rend_Industrial_%"] = g["Produzido_Kg"]    / g["Peso_Vivo_Kg"] * 100
    g["Taxa_Condena_%"]    = g["Peso_Condena_Kg"] / g["Peso_Vivo_Kg"] * 100
    g["Peso_Medio_Kg"]     = g["Peso_Vivo_Kg"]    / g["Cabecas"]
    return g.sort_values("Rend_Carcaca_%", ascending=False).reset_index(drop=True)


def serie_temporal(fato: pd.DataFrame, freq: str = "M") -> pd.DataFrame:
    """Evolução mensal (default) dos principais indicadores."""
    f = fato.set_index("Data").sort_index()
    g = (f.resample(freq)
          .agg(Peso_Vivo_Kg=("Peso_Vivo_Kg", "sum"),
               Peso_Condena_Kg=("Peso_Condena_Kg", "sum"),
               Produzido_Kg=("Total_Produzido_Kg", "sum"),
               Cabecas=("Cabecas", "sum"))
          .reset_index())
    g["Rend_Industrial_%"] = g["Produzido_Kg"]    / g["Peso_Vivo_Kg"] * 100
    g["Taxa_Condena_%"]    = g["Peso_Condena_Kg"] / g["Peso_Vivo_Kg"] * 100
    return g


if __name__ == "__main__":
    from data_loader import DataLoader
    from transformations import consolidar
    fato = consolidar(DataLoader().load())
    print(">>> KPIs executivos:")
    for k, v in kpis_executivos(fato).items():
        print(f"  {k:25s} {v:>15,.2f}")
    print("\n>>> Ranking parceiros:")
    print(kpis_por_parceiro(fato).to_string())
