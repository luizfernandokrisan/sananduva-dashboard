"""Análises avançadas: comparação MoM, geração de alertas e previsão simples.
   Sem dependências novas — só numpy + pandas."""
from __future__ import annotations
import numpy as np
import pandas as pd


# =============================================================
# 1) COMPARAÇÃO MoM (Month-over-Month)
# =============================================================
def comparar_mom(fato: pd.DataFrame) -> dict:
    """Compara último mês fechado vs mês anterior.
       Retorna dicionário com {kpi: {atual, anterior, variacao_pct, seta}}."""
    if fato.empty:
        return {}

    f = fato.copy()
    f["AnoMes"] = f["Data"].dt.to_period("M")
    meses = sorted(f["AnoMes"].unique())
    if len(meses) < 2:
        return {}

    atual, anterior = meses[-1], meses[-2]
    cur = f[f["AnoMes"] == atual]
    prv = f[f["AnoMes"] == anterior]

    def _mom(serie_cur, serie_prv, modo: str = "sum"):
        if modo == "sum":
            a, b = serie_cur.sum(), serie_prv.sum()
        else:  # ratio (já vem agregado)
            a, b = serie_cur, serie_prv
        var = ((a - b) / b * 100) if b else 0.0
        seta = "▲" if var > 0 else ("▼" if var < 0 else "▬")
        return {"atual": float(a), "anterior": float(b),
                "variacao_pct": float(var), "seta": seta}

    # Cálculo de ratios (agregados antes de comparar)
    rc_cur = (cur["Peso_Carcaca_Kg"].sum() / cur["Peso_Vivo_Kg"].sum() * 100) if cur["Peso_Vivo_Kg"].sum() else 0
    rc_prv = (prv["Peso_Carcaca_Kg"].sum() / prv["Peso_Vivo_Kg"].sum() * 100) if prv["Peso_Vivo_Kg"].sum() else 0
    ri_cur = (cur["Total_Produzido_Kg"].sum() / cur["Peso_Vivo_Kg"].sum() * 100) if cur["Peso_Vivo_Kg"].sum() else 0
    ri_prv = (prv["Total_Produzido_Kg"].sum() / prv["Peso_Vivo_Kg"].sum() * 100) if prv["Peso_Vivo_Kg"].sum() else 0
    tc_cur = (cur["Peso_Condena_Kg"].sum() / cur["Peso_Vivo_Kg"].sum() * 100) if cur["Peso_Vivo_Kg"].sum() else 0
    tc_prv = (prv["Peso_Condena_Kg"].sum() / prv["Peso_Vivo_Kg"].sum() * 100) if prv["Peso_Vivo_Kg"].sum() else 0

    return {
        "periodo_atual":   str(atual),
        "periodo_anterior": str(anterior),
        "cabecas":           _mom(cur["Cabecas"], prv["Cabecas"]),
        "peso_vivo":         _mom(cur["Peso_Vivo_Kg"], prv["Peso_Vivo_Kg"]),
        "rend_carcaca":      _mom(rc_cur, rc_prv, modo="ratio"),
        "rend_industrial":   _mom(ri_cur, ri_prv, modo="ratio"),
        "taxa_condena":      _mom(tc_cur, tc_prv, modo="ratio"),
    }


# =============================================================
# 2) ALERTAS — regras configuráveis
# =============================================================
THRESHOLDS = {
    "rend_carcaca_min":    75.0,   # abaixo disso = atenção
    "rend_industrial_min": 70.0,   # quando dados forem reais
    "taxa_condena_max":    2.0,    # acima disso = alerta
    "variacao_mom_max":    10.0,   # queda > 10% MoM em qualquer KPI
}


def gerar_alertas(fato: pd.DataFrame, mom: dict, thresholds: dict = None) -> list[dict]:
    """Retorna lista de alertas com severidade (info/warning/danger)."""
    t = {**THRESHOLDS, **(thresholds or {})}
    alertas = []

    # Regra 1: rendimento de carcaça MoM caiu muito
    rc = mom.get("rend_carcaca", {})
    if rc and rc["variacao_pct"] < -t["variacao_mom_max"]:
        alertas.append({
            "severidade": "danger",
            "icone": "bi-exclamation-octagon-fill",
            "titulo": "Queda forte no Rendimento de Carcaça",
            "msg": f"Caiu {rc['variacao_pct']:.1f}% vs mês anterior "
                   f"({rc['anterior']:.2f}% → {rc['atual']:.2f}%)",
        })

    # Regra 2: rendimento de carcaça absoluto baixo
    if rc and rc["atual"] < t["rend_carcaca_min"]:
        alertas.append({
            "severidade": "warning",
            "icone": "bi-exclamation-triangle-fill",
            "titulo": "Rendimento de Carcaça abaixo do alvo",
            "msg": f"{rc['atual']:.2f}% (alvo ≥ {t['rend_carcaca_min']:.1f}%)",
        })

    # Regra 3: taxa de condenação acima do limite
    tc = mom.get("taxa_condena", {})
    if tc and tc["atual"] > t["taxa_condena_max"]:
        alertas.append({
            "severidade": "danger",
            "icone": "bi-exclamation-octagon-fill",
            "titulo": "Taxa de Condenação acima do limite",
            "msg": f"{tc['atual']:.2f}% (limite {t['taxa_condena_max']:.2f}%)",
        })

    # Regra 4: parceiro abaixo da média do grupo (Rend. Carcaça)
    if not fato.empty:
        ult_mes = fato["Data"].max().to_period("M")
        f = fato[fato["Data"].dt.to_period("M") == ult_mes]
        rank = (f.groupby("Parceiro").apply(
            lambda x: x["Peso_Carcaca_Kg"].sum() / x["Peso_Vivo_Kg"].sum() * 100
        ).reset_index(name="rc"))
        if not rank.empty:
            media = rank["rc"].mean()
            piores = rank[rank["rc"] < media - 0.3]  # 0.3 p.p. abaixo da média
            for _, r in piores.iterrows():
                alertas.append({
                    "severidade": "info",
                    "icone": "bi-info-circle-fill",
                    "titulo": f"Parceiro {r['Parceiro']} abaixo da média",
                    "msg": f"Rend. carcaça {r['rc']:.2f}% vs média {media:.2f}% no mês",
                })

    if not alertas:
        alertas.append({
            "severidade": "success",
            "icone": "bi-check-circle-fill",
            "titulo": "Tudo dentro dos limites",
            "msg": "Nenhum desvio relevante detectado no último mês.",
        })

    return alertas


# =============================================================
# 3) PREVISÃO — tendência linear + banda histórica
# =============================================================
def prever(serie: pd.Series, n_meses: int = 3) -> pd.DataFrame:
    """Projeção simples: regressão linear (numpy.polyfit) + banda ±1σ histórico.
       Retorna DataFrame com colunas: Data, valor, lower, upper, tipo."""
    s = serie.dropna()
    if len(s) < 3:
        return pd.DataFrame()

    x = np.arange(len(s))
    coef = np.polyfit(x, s.values, deg=1)                 # tendência linear
    sigma = float(np.std(s.values - np.polyval(coef, x))) # erro do fit

    # Pontos futuros
    x_fut = np.arange(len(s), len(s) + n_meses)
    y_fut = np.polyval(coef, x_fut)

    datas_fut = pd.date_range(start=s.index[-1], periods=n_meses + 1,
                              freq="ME")[1:]

    hist = pd.DataFrame({"Data": s.index, "valor": s.values,
                         "lower": s.values, "upper": s.values,
                         "tipo": "histórico"})
    proj = pd.DataFrame({"Data": datas_fut, "valor": y_fut,
                         "lower": y_fut - sigma, "upper": y_fut + sigma,
                         "tipo": "projeção"})
    return pd.concat([hist, proj], ignore_index=True)


if __name__ == "__main__":
    from data_loader import DataLoader
    from transformations import consolidar
    from kpis import serie_temporal

    fato = consolidar(DataLoader().load())
    st = serie_temporal(fato, freq="ME").set_index("Data")

    print(">>> MoM:")
    mom = comparar_mom(fato)
    for k, v in mom.items():
        if isinstance(v, dict):
            print(f"  {k:18s} {v['anterior']:>12.2f} → {v['atual']:>12.2f}  "
                  f"{v['seta']} {v['variacao_pct']:+.2f}%")
        else:
            print(f"  {k}: {v}")

    print("\n>>> Alertas:")
    for a in gerar_alertas(fato, mom):
        print(f"  [{a['severidade'].upper():7s}] {a['titulo']} — {a['msg']}")

    print("\n>>> Previsão Peso_Vivo (próx. 3 meses):")
    print(prever(st["Peso_Vivo_Kg"], n_meses=3).tail(5).to_string())
