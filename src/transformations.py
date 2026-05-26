"""Transforma 3 planilhas em 1 fato consolidado: o 'fluxo macro' do negócio.
   Suíno → Pesa → Abate → Condena → Produção, agrupado por (Data, Parceiro)."""
import pandas as pd


def consolidar(dfs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Retorna uma tabela-fato granularidade (Data, Parceiro)."""
    abate = (dfs["Abate"]
             .groupby(["Data", "Parceiro"], as_index=False)
             .agg(Cabecas=("Quantidade", "sum"),
                  Peso_Vivo_Kg=("Peso_Vivo_Kg", "sum"),
                  Peso_Carcaca_Kg=("Peso_Carcaca_Quente_Kg", "sum")))

    condenas = (dfs["Condenas"]
                .groupby(["Data", "Parceiro"], as_index=False)
                .agg(Peso_Condena_Kg=("Peso_Condena", "sum")))

    producao = (dfs["Producao"]
                .groupby(["Data", "Parceiro"], as_index=False)
                .agg(Total_Produzido_Kg=("Total_Produzido", "sum")))

    fato = (abate
            .merge(condenas, on=["Data", "Parceiro"], how="left")
            .merge(producao, on=["Data", "Parceiro"], how="left")
            .fillna({"Peso_Condena_Kg": 0, "Total_Produzido_Kg": 0}))

    # Métricas derivadas no nível da linha (vetorizadas)
    fato["Peso_Liquido_Kg"]    = fato["Peso_Vivo_Kg"] - fato["Peso_Condena_Kg"]
    fato["Rend_Carcaca_%"]     = fato["Peso_Carcaca_Kg"]   / fato["Peso_Vivo_Kg"] * 100
    fato["Rend_Industrial_%"]  = fato["Total_Produzido_Kg"] / fato["Peso_Vivo_Kg"] * 100
    fato["Taxa_Condena_%"]     = fato["Peso_Condena_Kg"]   / fato["Peso_Vivo_Kg"] * 100
    fato["Aproveitamento_%"]   = fato["Peso_Liquido_Kg"]   / fato["Peso_Vivo_Kg"] * 100
    fato["Peso_Medio_Kg"]      = fato["Peso_Vivo_Kg"]      / fato["Cabecas"]

    # Dimensões temporais (úteis pros filtros do dashboard)
    fato["Ano"]    = fato["Data"].dt.year
    fato["Mes"]    = fato["Data"].dt.month
    fato["Semana"] = fato["Data"].dt.isocalendar().week.astype(int)
    fato["AnoMes"] = fato["Data"].dt.to_period("M").astype(str)

    return fato.sort_values(["Data", "Parceiro"]).reset_index(drop=True)


def mix_familia(df_producao: pd.DataFrame) -> pd.DataFrame:
    """Composição da produção por família de produto."""
    g = (df_producao.groupby("Família", as_index=False)
                    .agg(Total_Kg=("Total_Produzido", "sum")))
    g["Participacao_%"] = g["Total_Kg"] / g["Total_Kg"].sum() * 100
    return g.sort_values("Total_Kg", ascending=False).reset_index(drop=True)


if __name__ == "__main__":
    from data_loader import DataLoader
    dfs = DataLoader().load()
    fato = consolidar(dfs)
    print("Fato consolidado:", fato.shape)
    print(fato.head().to_string())
    print("\nMix por família:")
    print(mix_familia(dfs["Producao"]).to_string())
