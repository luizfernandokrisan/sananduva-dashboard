"""Modelos estatísticos para análise de carcaças suínas.

Referências teóricas:
- Irgang & Protas (1986). Peso ótimo de abate de suínos. Embrapa CNPSA.
  Pesq. agropec. bras. 21(12):1337-1345. Regressão clássica:
      RC(%) = 72,9 + 0,086 × P_abate  (R² = 0,65)
- Dutra Jr. et al. (2001). Estimativa de rendimentos de cortes comerciais
  por ultra-sonografia. Equações múltiplas com R² entre 0,97 e 0,99.
- Barbosa et al. (2005). Análise de componentes principais em 33
  variáveis de carcaça. R. Bras. Zootec. 34(6):2209-2217.
- Oliveira et al. (2015) via Embrapa: ponto ótimo econômico ~135 kg.
- NPPC/USDA: modelo polinomial com BF10, LMA e CWT.

Convenção: funções recebem DataFrame, devolvem dict com {coef, R², RMSE,
MAPE, p_valores, intervalo_confianca}. Nunca lançam exceção em produção:
em caso de dados insuficientes, devolvem dict vazio.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


# =================================================================
# 1) REGRESSÃO LINEAR SIMPLES — Irgang & Protas (1986)
# =================================================================
def regressao_linear_simples(x: pd.Series, y: pd.Series) -> dict:
    """Ajusta y = β₀ + β₁·x via OLS.

    Devolve dict com coeficientes, R², RMSE, MAPE, p-valores e IC 95%.
    Usa statsmodels.OLS (não scipy.linregress) porque devolve diagnóstico
    completo que precisamos pro dashboard de auditoria.
    """
    df = pd.concat([x, y], axis=1).dropna()
    if len(df) < 3:
        return {}
    x_clean = df.iloc[:, 0].values
    y_clean = df.iloc[:, 1].values

    X = sm.add_constant(x_clean)                  # adiciona intercepto
    modelo = sm.OLS(y_clean, X).fit()

    y_pred = modelo.predict(X)
    rmse = float(np.sqrt(np.mean((y_clean - y_pred) ** 2)))
    mape = float(np.mean(np.abs((y_clean - y_pred) / y_clean)) * 100)

    return {
        "tipo": "linear",
        "beta_0": float(modelo.params[0]),
        "beta_1": float(modelo.params[1]),
        "r2": float(modelo.rsquared),
        "r2_ajustado": float(modelo.rsquared_adj),
        "rmse": rmse,
        "mape": mape,
        "p_valor_beta_1": float(modelo.pvalues[1]),
        "ic_95_beta_1": tuple(modelo.conf_int(alpha=0.05)[1].tolist()),
        "n_observacoes": int(len(df)),
        "equacao_str": f"y = {modelo.params[0]:.3f} + {modelo.params[1]:.4f}·x",
        "x_range": (float(x_clean.min()), float(x_clean.max())),
        "y_pred": y_pred.tolist(),
        "x_vals": x_clean.tolist(),
        "y_vals": y_clean.tolist(),
    }


# =================================================================
# 2) REGRESSÃO POLINOMIAL QUADRÁTICA + PESO ÓTIMO
# =================================================================
def regressao_quadratica(x: pd.Series, y: pd.Series) -> dict:
    """Ajusta y = β₀ + β₁·x + β₂·x² e calcula ponto ótimo via derivada.

    P_ótimo = -β₁ / (2·β₂)  -- exato, não estimativa visual.
    Se β₂ > 0, é um mínimo (não há ótimo de maximização → devolve None).
    """
    df = pd.concat([x, y], axis=1).dropna()
    if len(df) < 4:
        return {}
    x_clean = df.iloc[:, 0].values
    y_clean = df.iloc[:, 1].values

    X = sm.add_constant(np.column_stack([x_clean, x_clean ** 2]))
    modelo = sm.OLS(y_clean, X).fit()
    b0, b1, b2 = modelo.params

    # Peso ótimo via derivada zerada
    p_otimo = None
    y_no_otimo = None
    if abs(b2) > 1e-12:
        p_otimo_calc = -b1 / (2 * b2)
        # Só faz sentido se cair dentro (ou perto) da faixa observada
        x_min, x_max = float(x_clean.min()), float(x_clean.max())
        margem = (x_max - x_min) * 0.5
        if (x_min - margem) <= p_otimo_calc <= (x_max + margem):
            if b2 < 0:  # parábola côncava → máximo
                p_otimo = float(p_otimo_calc)
                y_no_otimo = float(b0 + b1 * p_otimo + b2 * p_otimo ** 2)

    y_pred = modelo.predict(X)
    rmse = float(np.sqrt(np.mean((y_clean - y_pred) ** 2)))
    mape = float(np.mean(np.abs((y_clean - y_pred) / y_clean)) * 100)

    # Curva suavizada para plotagem
    x_smooth = np.linspace(x_clean.min(), x_clean.max(), 100)
    y_smooth = b0 + b1 * x_smooth + b2 * x_smooth ** 2

    return {
        "tipo": "quadratico",
        "beta_0": float(b0), "beta_1": float(b1), "beta_2": float(b2),
        "r2": float(modelo.rsquared),
        "r2_ajustado": float(modelo.rsquared_adj),
        "rmse": rmse, "mape": mape,
        "p_valor_beta_1": float(modelo.pvalues[1]),
        "p_valor_beta_2": float(modelo.pvalues[2]),
        "peso_otimo": p_otimo,
        "y_no_otimo": y_no_otimo,
        "n_observacoes": int(len(df)),
        "equacao_str": (f"y = {b0:.3f} + {b1:.4f}·x + {b2:.6f}·x²"),
        "x_smooth": x_smooth.tolist(),
        "y_smooth": y_smooth.tolist(),
        "x_vals": x_clean.tolist(),
        "y_vals": y_clean.tolist(),
    }


# =================================================================
# 3) REGRESSÃO LINEAR MÚLTIPLA — múltiplos preditores
# =================================================================
def regressao_multipla(df: pd.DataFrame, y_col: str, x_cols: list[str]) -> dict:
    """Y = β₀ + Σ βᵢ·Xᵢ + ε. Devolve coeficientes com p-valores,
    diagnóstico (Durbin-Watson, Jarque-Bera) e teste F do modelo."""
    dados = df[[y_col] + x_cols].dropna()
    if len(dados) < len(x_cols) + 2:
        return {}

    y = dados[y_col].values
    X = sm.add_constant(dados[x_cols].values)
    modelo = sm.OLS(y, X).fit()

    coefs = []
    nomes = ["intercepto"] + x_cols
    for i, nome in enumerate(nomes):
        coefs.append({
            "variavel": nome,
            "coeficiente": float(modelo.params[i]),
            "erro_padrao": float(modelo.bse[i]),
            "p_valor": float(modelo.pvalues[i]),
            "significante": bool(modelo.pvalues[i] < 0.05),
            "ic_95_inf": float(modelo.conf_int(alpha=0.05)[i][0]),
            "ic_95_sup": float(modelo.conf_int(alpha=0.05)[i][1]),
        })

    y_pred = modelo.predict(X)
    rmse = float(np.sqrt(np.mean((y - y_pred) ** 2)))

    return {
        "tipo": "multipla",
        "y_col": y_col, "x_cols": x_cols,
        "coeficientes": coefs,
        "r2": float(modelo.rsquared),
        "r2_ajustado": float(modelo.rsquared_adj),
        "rmse": rmse,
        "f_estatistica": float(modelo.fvalue),
        "f_p_valor": float(modelo.f_pvalue),
        "durbin_watson": float(sm.stats.durbin_watson(modelo.resid)),
        "n_observacoes": int(len(dados)),
        "y_real": y.tolist(),
        "y_pred": y_pred.tolist(),
    }


# =================================================================
# 4) MATRIZ DE CORRELAÇÃO
# =================================================================
def matriz_correlacao(df: pd.DataFrame, colunas: list[str],
                      metodo: str = "pearson") -> pd.DataFrame:
    """Pearson (default), Spearman (não-paramétrico) ou Kendall."""
    return df[colunas].corr(method=metodo).round(3)


# =================================================================
# 5) ANÁLISE DE COMPONENTES PRINCIPAIS (PCA)
# =================================================================
def aplicar_pca(df: pd.DataFrame, colunas: list[str],
                n_componentes: int = None) -> dict:
    """PCA padronizando via Z-score (igual Barbosa et al. 2005).
    Sem n_componentes → mantém todos. Critério Jolliffe (autovalor < 0.7)
    aplicado pra sugerir descarte."""
    dados = df[colunas].dropna()
    if len(dados) < 3 or len(colunas) < 2:
        return {}

    scaler = StandardScaler()
    X_std = scaler.fit_transform(dados.values)

    n_max = min(len(colunas), len(dados))
    n = n_componentes or n_max
    pca = PCA(n_components=n)
    X_pca = pca.fit_transform(X_std)

    autovalores = pca.explained_variance_.tolist()
    var_explicada = pca.explained_variance_ratio_.tolist()
    var_acumulada = np.cumsum(var_explicada).tolist()

    # Loadings: contribuição de cada variável original em cada CP
    loadings = pd.DataFrame(
        pca.components_.T * np.sqrt(pca.explained_variance_),
        index=colunas,
        columns=[f"CP{i+1}" for i in range(n)],
    )

    # Critério Jolliffe — sugere descarte
    descartaveis = [c for c, av in zip(colunas, autovalores) if av < 0.7]

    return {
        "scores": X_pca.tolist(),
        "loadings": loadings.round(3).to_dict(),
        "autovalores": autovalores,
        "variancia_explicada": var_explicada,
        "variancia_acumulada": var_acumulada,
        "variaveis_descartaveis": descartaveis,
        "n_observacoes": int(len(dados)),
        "indices_observacoes": dados.index.tolist(),
        "colunas": colunas,
    }


# =================================================================
# 6) ESTATÍSTICA DESCRITIVA + TESTE DE NORMALIDADE
# =================================================================
def descritiva(serie: pd.Series) -> dict:
    """Estatísticas básicas + Shapiro-Wilk pra normalidade."""
    s = serie.dropna()
    if len(s) < 3:
        return {}

    from scipy import stats as scipy_stats
    stat, p_norm = scipy_stats.shapiro(s) if len(s) <= 5000 else (np.nan, np.nan)

    return {
        "n": int(len(s)),
        "media": float(s.mean()),
        "mediana": float(s.median()),
        "desvio_padrao": float(s.std()),
        "cv_pct": float(s.std() / s.mean() * 100) if s.mean() else 0.0,
        "minimo": float(s.min()),
        "maximo": float(s.max()),
        "q1": float(s.quantile(0.25)),
        "q3": float(s.quantile(0.75)),
        "iqr": float(s.quantile(0.75) - s.quantile(0.25)),
        "assimetria": float(s.skew()),
        "curtose": float(s.kurt()),
        "shapiro_p": float(p_norm) if not np.isnan(p_norm) else None,
        "normal_5pct": bool(p_norm > 0.05) if not np.isnan(p_norm) else None,
    }


if __name__ == "__main__":
    from data_loader import DataLoader
    from transformations import consolidar
    fato = consolidar(DataLoader().load())

    print("=== 1) REGRESSÃO LINEAR SIMPLES ===")
    r = regressao_linear_simples(fato["Peso_Medio_Kg"], fato["Rend_Carcaca_%"])
    if r:
        print(f"  {r['equacao_str']}")
        print(f"  R²={r['r2']:.4f}  RMSE={r['rmse']:.4f}  p(β₁)={r['p_valor_beta_1']:.4f}")

    print("\n=== 2) REGRESSÃO QUADRÁTICA ===")
    r = regressao_quadratica(fato["Peso_Medio_Kg"], fato["Rend_Carcaca_%"])
    if r:
        print(f"  {r['equacao_str']}")
        print(f"  R²={r['r2']:.4f}  RMSE={r['rmse']:.4f}")
        if r["peso_otimo"]:
            print(f"  PESO ÓTIMO: {r['peso_otimo']:.2f} kg → rend = {r['y_no_otimo']:.2f}%")
        else:
            print(f"  (peso ótimo fora da faixa observada ou modelo não côncavo)")

    print("\n=== 3) REGRESSÃO MÚLTIPLA ===")
    r = regressao_multipla(fato, "Rend_Industrial_%",
                            ["Peso_Medio_Kg", "Cabecas", "Taxa_Condena_%"])
    if r:
        print(f"  R²={r['r2']:.4f}  R²_aj={r['r2_ajustado']:.4f}  F={r['f_estatistica']:.2f}")
        for c in r["coeficientes"]:
            sig = "*" if c["significante"] else " "
            print(f"   {sig} {c['variavel']:20s}  β={c['coeficiente']:>10.4f}  p={c['p_valor']:.4f}")

    print("\n=== 4) MATRIZ DE CORRELAÇÃO ===")
    cols = ["Peso_Vivo_Kg", "Peso_Carcaca_Kg", "Total_Produzido_Kg",
            "Peso_Condena_Kg", "Cabecas", "Peso_Medio_Kg"]
    print(matriz_correlacao(fato, cols).to_string())

    print("\n=== 5) PCA ===")
    p = aplicar_pca(fato, cols)
    if p:
        for i, (ve, va) in enumerate(zip(p["variancia_explicada"], p["variancia_acumulada"])):
            print(f"  CP{i+1}: {ve*100:5.2f}%  (acumulado: {va*100:5.2f}%)")

    print("\n=== 6) DESCRITIVA — Rend_Carcaca_% ===")
    d = descritiva(fato["Rend_Carcaca_%"])
    sp = f"{d['shapiro_p']:.4f}" if d['shapiro_p'] else "N/A"
    print(f"  n={d['n']}  μ={d['media']:.2f}  σ={d['desvio_padrao']:.4f}  "
          f"CV={d['cv_pct']:.2f}%  Shapiro p={sp}")
