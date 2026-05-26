"""Callbacks da página de Análise Estatística."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, html, dash_table
import dash_bootstrap_components as dbc
from flask_login import current_user

from config import CORES
from stats_models import (regressao_linear_simples, regressao_quadratica,
                        regressao_multipla, matriz_correlacao, aplicar_pca,
                        descritiva)


COLUNAS_ANALISE = ["Peso_Vivo_Kg", "Peso_Carcaca_Kg", "Total_Produzido_Kg",
                   "Peso_Condena_Kg", "Cabecas", "Peso_Medio_Kg"]


# ============ Helpers de formatação ============
def _eq_box(titulo, equacao, metricas, cor=None):
    cor = cor or CORES["primaria"]
    return html.Div(style={
        "background": f"{cor}08", "borderLeft": f"3px solid {cor}",
        "padding": "12px 16px", "borderRadius": "8px",
    }, children=[
        html.Div(titulo, style={"fontSize": "11px", "fontWeight": 700,
                                "textTransform": "uppercase",
                                "letterSpacing": "0.06em",
                                "color": CORES["texto_fraco"]}),
        html.Div(equacao, style={"fontFamily": "'JetBrains Mono', Consolas, monospace",
                                 "fontSize": "14px", "fontWeight": 600,
                                 "margin": "6px 0 8px", "color": cor}),
        html.Div(metricas, style={"fontSize": "12px",
                                  "color": CORES["texto"]}),
    ])


def _interpretacao(titulo, texto, recomendacao=None, severidade="info"):
    cores_sev = {"info": "#1976D2", "success": CORES["secundaria"],
                 "warning": "#F57C00", "danger": CORES["alerta"]}
    cor = cores_sev[severidade]
    children = [
        html.Div([
            html.I(className="bi bi-lightbulb-fill",
                   style={"color": cor, "marginRight": "8px"}),
            html.Strong(titulo, style={"color": cor}),
        ]),
        html.Div(texto, style={"fontSize": "13px", "marginTop": "6px",
                                "color": CORES["texto"]}),
    ]
    if recomendacao:
        children.append(html.Div([
            html.I(className="bi bi-arrow-right-circle-fill",
                   style={"color": CORES["primaria"], "marginRight": "6px"}),
            html.Strong("Recomendação: "), recomendacao,
        ], style={"fontSize": "13px", "marginTop": "8px",
                  "fontWeight": 500}))
    return html.Div(children, style={
        "background": f"{cor}10", "borderLeft": f"3px solid {cor}",
        "padding": "12px 16px", "borderRadius": "8px",
    })


def register_callbacks_analise(app, fato, dfs):

    @app.callback(Output("user-badge-analise", "children"),
                  Input("ana-periodo", "start_date"))
    def _badge(_):
        if not current_user.is_authenticated:
            return ""
        return [
            html.I(className="bi bi-person-circle",
                   style={"fontSize": "16px", "color": "white"}),
            html.Span(current_user.nome,
                      style={"color": "white", "fontWeight": 600,
                             "fontSize": "13px"}),
            html.A([html.I(className="bi bi-box-arrow-right"), " Sair"],
                   href="/logout",
                   style={"color": "white", "marginLeft": "8px",
                          "fontSize": "12px", "textDecoration": "none",
                          "padding": "4px 10px",
                          "background": "rgba(255,255,255,0.18)",
                          "borderRadius": "999px", "fontWeight": 500}),
        ]

    @app.callback(
        Output("ana-grafico-pesootimo", "figure"),
        Output("ana-equacao-linear", "children"),
        Output("ana-equacao-quadratica", "children"),
        Output("ana-interpretacao-pesootimo", "children"),
        Output("ana-grafico-correlacao", "figure"),
        Output("ana-interpretacao-correlacao", "children"),
        Output("ana-grafico-pca", "figure"),
        Output("ana-tabela-variancia", "children"),
        Output("ana-interpretacao-pca", "children"),
        Output("ana-tabela-multipla", "children"),
        Output("ana-grafico-residuos", "figure"),
        Output("ana-interpretacao-multipla", "children"),
        Output("ana-grafico-dist", "figure"),
        Output("ana-tabela-descritiva", "children"),
        Input("ana-periodo", "start_date"),
        Input("ana-periodo", "end_date"),
        Input("ana-parceiros", "value"),
        Input("ana-metrica-dist", "value"),
    )
    def _atualizar_analise(start, end, parceiros, metrica_dist):

        m = ((fato["Data"] >= start) & (fato["Data"] <= end)
             & (fato["Parceiro"].isin(parceiros or [])))
        f = fato.loc[m].copy()

        # ============ ANÁLISE 1: PESO ÓTIMO ============
        lin = regressao_linear_simples(f["Peso_Medio_Kg"], f["Rend_Carcaca_%"])
        qua = regressao_quadratica(f["Peso_Medio_Kg"], f["Rend_Carcaca_%"])

        fig_po = go.Figure()
        if lin and qua:
            # Pontos observados
            fig_po.add_trace(go.Scatter(
                x=qua["x_vals"], y=qua["y_vals"], mode="markers",
                name="Observados", marker=dict(size=8, color=CORES["primaria"],
                                                opacity=0.5,
                                                line=dict(color="white", width=1)),
                hovertemplate="Peso: %{x:.1f} kg<br>Rend: %{y:.2f}%<extra></extra>"))
            # Linha linear
            x_l = np.linspace(min(lin["x_vals"]), max(lin["x_vals"]), 50)
            y_l = lin["beta_0"] + lin["beta_1"] * x_l
            fig_po.add_trace(go.Scatter(
                x=x_l, y=y_l, mode="lines",
                name=f"Linear (R²={lin['r2']:.3f})",
                line=dict(color="#1976D2", width=2, dash="dot")))
            # Curva quadrática
            fig_po.add_trace(go.Scatter(
                x=qua["x_smooth"], y=qua["y_smooth"], mode="lines",
                name=f"Quadrática (R²={qua['r2']:.3f})",
                line=dict(color=CORES["alerta"], width=3)))
            # Peso ótimo
            if qua["peso_otimo"]:
                fig_po.add_trace(go.Scatter(
                    x=[qua["peso_otimo"]], y=[qua["y_no_otimo"]],
                    mode="markers+text",
                    marker=dict(size=18, color=CORES["destaque"],
                                symbol="star",
                                line=dict(color=CORES["alerta"], width=2)),
                    text=[f"  Ótimo: {qua['peso_otimo']:.1f} kg"],
                    textposition="top right", textfont=dict(size=12, color=CORES["alerta"]),
                    name="Peso ótimo", hoverinfo="skip"))
        fig_po.update_layout(
            template="plotly_white", height=400,
            margin=dict(l=10, r=10, t=10, b=20),
            xaxis_title="Peso Médio (kg)", yaxis_title="Rendimento de Carcaça (%)",
            font=dict(family="Inter, sans-serif", size=12),
            legend=dict(orientation="h", y=-0.18),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            hoverlabel=dict(bgcolor="white", font_family="Inter",
                            bordercolor="#E5E7EB"))

        # Equações
        eq_lin = _eq_box("Regressão Linear",
                         lin["equacao_str"] if lin else "(sem dados)",
                         (f"R² = {lin['r2']:.4f}  ·  RMSE = {lin['rmse']:.3f}  ·  "
                          f"p(β₁) = {lin['p_valor_beta_1']:.4f}") if lin else "",
                         cor="#1976D2") if lin else html.Div()

        otimo_txt = (f"  ·  Peso ótimo = {qua['peso_otimo']:.2f} kg "
                     f"(rend = {qua['y_no_otimo']:.2f}%)") if (qua and qua["peso_otimo"]) else ""
        eq_qua = _eq_box("Regressão Quadrática",
                         qua["equacao_str"] if qua else "(sem dados)",
                         (f"R² = {qua['r2']:.4f}  ·  RMSE = {qua['rmse']:.3f}"
                          f"{otimo_txt}") if qua else "",
                         cor=CORES["alerta"]) if qua else html.Div()

        # Interpretação
        if qua and qua["peso_otimo"]:
            sev = "warning" if qua["r2"] < 0.3 else "success"
            interp_po = _interpretacao(
                f"Peso ótimo identificado: {qua['peso_otimo']:.1f} kg",
                f"O modelo quadrático sugere maximizar rendimento de carcaça abatendo suínos "
                f"em torno de {qua['peso_otimo']:.0f} kg (rendimento previsto: {qua['y_no_otimo']:.2f}%). "
                f"A literatura (Embrapa, Oliveira et al. 2015) aponta 130-135 kg como ponto "
                f"ótimo econômico. R² = {qua['r2']:.3f} — "
                + ("modelo robusto." if qua["r2"] >= 0.7
                   else f"modelo com baixo poder explicativo ({qua['r2']*100:.1f}% da variância), "
                        f"esperado com dados sintéticos. Revalidar com dados reais."),
                recomendacao=(
                    f"Pactuar com fornecedores faixa de abate {qua['peso_otimo']-5:.0f}-"
                    f"{qua['peso_otimo']+5:.0f} kg para próxima safra; monitorar rendimento "
                    f"de carcaça semanalmente para confirmar o ponto ótimo na operação."),
                severidade=sev)
        else:
            interp_po = _interpretacao(
                "Peso ótimo não identificável no intervalo observado",
                "O modelo não detectou ponto de máximo dentro da faixa de pesos da amostra. "
                "Pode indicar que a operação ainda não atingiu o platô — ou que dados "
                "precisam de mais variabilidade.",
                severidade="warning")

        # ============ ANÁLISE 2: CORRELAÇÃO ============
        cor_mat = matriz_correlacao(f, COLUNAS_ANALISE)
        fig_corr = go.Figure(data=go.Heatmap(
            z=cor_mat.values, x=cor_mat.columns, y=cor_mat.index,
            colorscale=[[0, CORES["alerta"]], [0.5, "white"], [1, CORES["primaria"]]],
            zmid=0, zmin=-1, zmax=1,
            text=cor_mat.round(2).values,
            texttemplate="%{text}", textfont=dict(size=11),
            hovertemplate="%{y} × %{x}<br>r = %{z:.3f}<extra></extra>"))
        fig_corr.update_layout(template="plotly_white", height=400,
                               margin=dict(l=10, r=10, t=10, b=20),
                               font=dict(family="Inter, sans-serif", size=11),
                               xaxis=dict(tickangle=-30),
                               plot_bgcolor="rgba(0,0,0,0)",
                               paper_bgcolor="rgba(0,0,0,0)")

        # Identifica par mais correlacionado (excluindo diagonal)
        cm_off = cor_mat.where(~np.eye(len(cor_mat), dtype=bool)).abs()
        idx_max = cm_off.stack().idxmax()
        val_max = cor_mat.loc[idx_max[0], idx_max[1]]
        interp_corr = _interpretacao(
            f"Correlação mais forte: {idx_max[0]} × {idx_max[1]} (r = {val_max:.3f})",
            "Correlação > 0,9 entre duas variáveis indica redundância — "
            "uma pode ser usada para prever a outra. Correlação > 0,7 é considerada forte; "
            "0,5-0,7 moderada; <0,3 fraca. Valores próximos de 1,00 entre Peso Vivo e "
            "Peso Carcaça são esperados (PCQ ~76% do PV).",
            recomendacao=("Use as variáveis mais correlacionadas com seu KPI-alvo "
                          "como features prioritárias em modelos preditivos."),
            severidade="info")

        # ============ ANÁLISE 3: PCA ============
        pca_res = aplicar_pca(f, COLUNAS_ANALISE)
        fig_pca = go.Figure()
        if pca_res:
            scores = np.array(pca_res["scores"])
            idx_obs = pca_res["indices_observacoes"]
            parceiros_obs = f.loc[idx_obs, "Parceiro"].values
            cores_p = {"BRF": "#1976D2", "ECOFRIGO": CORES["primaria"],
                       "JBS": "#D32F2F", "PAMPLONA": "#7B1FA2"}
            for p in np.unique(parceiros_obs):
                mask = parceiros_obs == p
                fig_pca.add_trace(go.Scatter(
                    x=scores[mask, 0], y=scores[mask, 1], mode="markers",
                    name=p, marker=dict(size=10, color=cores_p.get(p, "#666"),
                                         opacity=0.7,
                                         line=dict(color="white", width=1)),
                    hovertemplate=f"<b>{p}</b><br>CP1: %{{x:.2f}}<br>CP2: %{{y:.2f}}<extra></extra>"))
            ve1 = pca_res["variancia_explicada"][0] * 100
            ve2 = pca_res["variancia_explicada"][1] * 100
            fig_pca.update_layout(
                template="plotly_white", height=400,
                margin=dict(l=10, r=10, t=10, b=20),
                xaxis_title=f"CP1 ({ve1:.1f}% da variância)",
                yaxis_title=f"CP2 ({ve2:.1f}% da variância)",
                font=dict(family="Inter, sans-serif", size=12),
                legend=dict(orientation="h", y=-0.18),
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")

            # Tabela de variância
            tabela_var = dash_table.DataTable(
                data=[{"Componente": f"CP{i+1}",
                       "Autovalor": f"{av:.3f}",
                       "Variância %": f"{ve*100:.2f}%",
                       "Acumulado %": f"{va*100:.2f}%"}
                      for i, (av, ve, va) in enumerate(zip(
                          pca_res["autovalores"],
                          pca_res["variancia_explicada"],
                          pca_res["variancia_acumulada"]))],
                columns=[{"name": c, "id": c}
                         for c in ["Componente", "Autovalor",
                                   "Variância %", "Acumulado %"]],
                style_cell={"fontFamily": "Inter, sans-serif",
                            "fontSize": "12px", "padding": "6px",
                            "textAlign": "center"},
                style_header={"backgroundColor": CORES["primaria"],
                              "color": "white", "fontWeight": "bold"},
                style_data_conditional=[{"if": {"row_index": "odd"},
                                         "backgroundColor": "#FAFAFA"}])

            n_pra_85 = next((i+1 for i, v in enumerate(pca_res["variancia_acumulada"])
                             if v >= 0.85), len(pca_res["variancia_acumulada"]))
            descartaveis = pca_res["variaveis_descartaveis"]
            interp_pca = _interpretacao(
                f"{n_pra_85} componentes explicam ≥ 85% da variância",
                f"PCA reduziu {len(COLUNAS_ANALISE)} variáveis para {n_pra_85} dimensões "
                f"preservando "
                f"{pca_res['variancia_acumulada'][n_pra_85-1]*100:.1f}% da informação. "
                f"Pelo critério Jolliffe (autovalor < 0.7), "
                + (f"variáveis candidatas a descarte: {', '.join(descartaveis)}."
                   if descartaveis else "nenhuma variável é redundante."),
                recomendacao=("Use CP1 e CP2 como features compactas em modelos de "
                              "classificação de parceiros ou detecção de anomalias."),
                severidade="info")
        else:
            tabela_var = html.Div("Dados insuficientes para PCA.")
            interp_pca = html.Div()

        # ============ ANÁLISE 4: REGRESSÃO MÚLTIPLA ============
        mlt = regressao_multipla(f, "Rend_Industrial_%",
                                  ["Peso_Medio_Kg", "Cabecas", "Taxa_Condena_%"])
        if mlt:
            linhas_tab = []
            for c in mlt["coeficientes"]:
                sig = "✓" if c["significante"] else "—"
                linhas_tab.append({
                    "Variável": c["variavel"],
                    "Coeficiente": f"{c['coeficiente']:.4f}",
                    "Erro padrão": f"{c['erro_padrao']:.4f}",
                    "p-valor": f"{c['p_valor']:.4f}",
                    "IC 95%": f"[{c['ic_95_inf']:.3f}; {c['ic_95_sup']:.3f}]",
                    "Sig. (5%)": sig,
                })
            tab_mlt = dash_table.DataTable(
                data=linhas_tab,
                columns=[{"name": c, "id": c} for c in linhas_tab[0].keys()],
                style_cell={"fontFamily": "Inter, sans-serif",
                            "fontSize": "12px", "padding": "8px"},
                style_header={"backgroundColor": CORES["primaria"],
                              "color": "white", "fontWeight": "bold"},
                style_data_conditional=[
                    {"if": {"filter_query": "{Sig. (5%)} = '✓'"},
                     "backgroundColor": "#E8F5E9"},
                    {"if": {"row_index": "odd",
                            "filter_query": "{Sig. (5%)} != '✓'"},
                     "backgroundColor": "#FAFAFA"},
                ])

            # Gráfico de resíduos
            resid = np.array(mlt["y_real"]) - np.array(mlt["y_pred"])
            fig_res = go.Figure()
            fig_res.add_trace(go.Scatter(
                x=mlt["y_pred"], y=resid, mode="markers",
                marker=dict(size=8, color=CORES["primaria"], opacity=0.6,
                            line=dict(color="white", width=1)),
                hovertemplate="Predito: %{x:.2f}<br>Resíduo: %{y:.3f}<extra></extra>",
                name="Resíduos"))
            fig_res.add_hline(y=0, line=dict(color=CORES["alerta"],
                                              width=1, dash="dash"))
            fig_res.update_layout(
                template="plotly_white", height=280,
                margin=dict(l=10, r=10, t=20, b=20),
                title="Gráfico de Resíduos (deve estar centrado em 0, sem padrão)",
                title_font=dict(size=12),
                xaxis_title="Valor predito", yaxis_title="Resíduo",
                font=dict(family="Inter, sans-serif", size=11),
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                showlegend=False)

            sig_vars = [c["variavel"] for c in mlt["coeficientes"]
                        if c["significante"] and c["variavel"] != "intercepto"]
            interp_mlt = _interpretacao(
                f"R² ajustado = {mlt['r2_ajustado']:.3f}  ·  "
                f"F = {mlt['f_estatistica']:.2f} (p = {mlt['f_p_valor']:.4f})",
                ("Variáveis significantes (p<0,05): " + ", ".join(sig_vars) + "."
                 if sig_vars else "Nenhuma variável foi significante a 5%. ")
                + f" Durbin-Watson = {mlt['durbin_watson']:.2f} "
                + ("(sem autocorrelação)." if 1.5 <= mlt['durbin_watson'] <= 2.5
                   else "(possível autocorrelação dos resíduos)."),
                recomendacao=("Concentre esforços operacionais nas variáveis significantes; "
                              "as não-significantes não impactam o rendimento na amostra atual."
                              if sig_vars else
                              "Coletar mais dados ou incluir AOL/ET para melhorar o modelo."),
                severidade="success" if mlt["r2_ajustado"] >= 0.5 else "warning")
        else:
            tab_mlt = html.Div("Dados insuficientes para regressão múltipla.")
            fig_res = go.Figure()
            interp_mlt = html.Div()

        # ============ ANÁLISE 5: DISTRIBUIÇÃO ============
        desc_geral = descritiva(f[metrica_dist])
        fig_dist = go.Figure()
        cores_p = {"BRF": "#1976D2", "ECOFRIGO": CORES["primaria"],
                   "JBS": "#D32F2F", "PAMPLONA": "#7B1FA2"}
        for p in sorted(f["Parceiro"].unique()):
            fig_dist.add_trace(go.Box(
                y=f.loc[f["Parceiro"] == p, metrica_dist],
                name=p, marker_color=cores_p.get(p, "#666"),
                boxmean="sd", boxpoints="outliers"))
        fig_dist.update_layout(
            template="plotly_white", height=400,
            margin=dict(l=10, r=10, t=10, b=20),
            yaxis_title=metrica_dist.replace("_", " "),
            font=dict(family="Inter, sans-serif", size=12),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            showlegend=False)

        if desc_geral:
            linhas_desc = [{
                "Estatística": k,
                "Valor": (f"{v:.4f}" if isinstance(v, float) else str(v))
            } for k, v in [
                ("n (observações)", desc_geral["n"]),
                ("Média (μ)", desc_geral["media"]),
                ("Mediana", desc_geral["mediana"]),
                ("Desvio padrão (σ)", desc_geral["desvio_padrao"]),
                ("Coef. de variação (CV)", f"{desc_geral['cv_pct']:.2f}%"),
                ("Mínimo", desc_geral["minimo"]),
                ("Máximo", desc_geral["maximo"]),
                ("Q1 (25%)", desc_geral["q1"]),
                ("Q3 (75%)", desc_geral["q3"]),
                ("Assimetria (skew)", desc_geral["assimetria"]),
                ("Curtose", desc_geral["curtose"]),
                ("Shapiro-Wilk (p-valor)",
                 f"{desc_geral['shapiro_p']:.4f}" if desc_geral["shapiro_p"] else "N/A"),
                ("Distribuição normal? (5%)",
                 "Sim" if desc_geral["normal_5pct"] else "Não"),
            ]]
            tab_desc = dash_table.DataTable(
                data=linhas_desc,
                columns=[{"name": c, "id": c}
                         for c in ["Estatística", "Valor"]],
                style_cell={"fontFamily": "Inter, sans-serif",
                            "fontSize": "12px", "padding": "6px 12px"},
                style_header={"backgroundColor": CORES["primaria"],
                              "color": "white", "fontWeight": "bold"},
                style_data_conditional=[{"if": {"row_index": "odd"},
                                         "backgroundColor": "#FAFAFA"}])
        else:
            tab_desc = html.Div()

        return (fig_po, eq_lin, eq_qua, interp_po,
                fig_corr, interp_corr,
                fig_pca, tabela_var, interp_pca,
                tab_mlt, fig_res, interp_mlt,
                fig_dist, tab_desc)
