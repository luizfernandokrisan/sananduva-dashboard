"""Callbacks — reagem aos filtros e atualizam todos os componentes."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Input, Output, html, dash_table
import dash_bootstrap_components as dbc
from flask_login import current_user

from config import CORES
from kpis import kpis_executivos, kpis_por_parceiro, serie_temporal
from transformations import mix_familia
from analytics import comparar_mom, gerar_alertas, prever
from components.kpi_cards import card_kpi


def _fmt_int(v):    return f"{v:,.0f}".replace(",", ".")
def _fmt_pct(v):    return f"{v:,.2f}%".replace(".", ",")
def _fmt_kg(v):
    if v >= 1_000_000: return f"{v/1_000_000:,.2f} M kg".replace(".", ",")
    if v >= 1_000:     return f"{v/1_000:,.2f} k kg".replace(".", ",")
    return f"{v:,.0f} kg"


def _banner_alertas(alertas):
    cores_map = {"danger": CORES["alerta"], "warning": "#F57C00",
                 "info": "#1976D2", "success": CORES["secundaria"]}
    items = []
    for i, a in enumerate(alertas):
        items.append(dbc.Col(
            html.Div(className="alert-item", style={
                "background": cores_map[a["severidade"]] + "12",
                "borderLeft": f"3px solid {cores_map[a['severidade']]}",
                "padding": "12px 16px", "borderRadius": "10px",
                "display": "flex", "gap": "12px", "alignItems": "center",
                "height": "100%", "animationDelay": f"{i*60}ms",
            }, children=[
                html.I(className=f"bi {a['icone']}",
                       style={"color": cores_map[a["severidade"]], "fontSize": "20px"}),
                html.Div([
                    html.Div(a["titulo"], style={"fontSize": "13px",
                                                  "fontWeight": 600,
                                                  "color": CORES["texto"]}),
                    html.Div(a["msg"], style={"fontSize": "11px",
                                              "color": CORES["texto_fraco"],
                                              "marginTop": "2px"}),
                ]),
            ]),
            md=6, lg=4,
        ))
    return dbc.Row(items, className="g-2")


def register_callbacks(app, fato, dfs):

    @app.callback(Output("user-badge", "children"),
                  Input("filtro-periodo", "start_date"))
    def _user_badge(_):
        if not current_user.is_authenticated:
            return ""
        return [
            html.I(className="bi bi-person-circle",
                   style={"fontSize": "16px", "color": "white"}),
            html.Span(current_user.nome,
                      style={"color": "white", "fontWeight": 600, "fontSize": "13px"}),
            html.Span(f"· {current_user.role}",
                      style={"color": "rgba(255,255,255,0.7)", "fontSize": "11px",
                             "marginLeft": "2px"}),
            html.A([html.I(className="bi bi-box-arrow-right"), " Sair"],
                   href="/logout",
                   style={"color": "white", "marginLeft": "8px", "fontSize": "12px",
                          "textDecoration": "none", "padding": "4px 10px",
                          "background": "rgba(255,255,255,0.18)",
                          "borderRadius": "999px",
                          "fontWeight": 500}),
        ]

    @app.callback(
        Output("row-cards", "children"),
        Output("banner-alertas", "children"),
        Output("grafico-temporal", "figure"),
        Output("grafico-ranking", "figure"),
        Output("grafico-mix", "figure"),
        Output("tabela-drilldown", "children"),
        Output("header-periodo", "children"),
        Input("filtro-periodo", "start_date"),
        Input("filtro-periodo", "end_date"),
        Input("filtro-parceiro", "value"),
        Input("filtro-tipo", "value"),
        Input("filtro-familia", "value"),
        Input("seletor-metrica-temporal", "value"),
    )
    def _atualizar(start, end, parceiros, tipos, familias, metrica):
        m = ((fato["Data"] >= start) & (fato["Data"] <= end)
             & (fato["Parceiro"].isin(parceiros or [])))
        f = fato.loc[m].copy()

        k = kpis_executivos(f)
        mom = comparar_mom(f)
        def _dv(c): return mom.get(c, {}).get("variacao_pct")

        cards = [
            dbc.Col(card_kpi("Cabeças Abatidas",
                             _fmt_int(k.get("cabecas_abatidas", 0)),
                             f"Peso médio: {k.get('peso_medio_kg', 0):,.1f} kg".replace(".", ","),
                             icone="bi-collection-fill", cor=CORES["primaria"],
                             delta_pct=_dv("cabecas"), delta_bom="up"), md=3),
            dbc.Col(card_kpi("Peso Vivo Abatido",
                             _fmt_kg(k.get("peso_vivo_total_kg", 0)),
                             f"Carcaça: {_fmt_kg(k.get('peso_carcaca_total_kg', 0))}",
                             icone="bi-box-seam", cor=CORES["secundaria"],
                             delta_pct=_dv("peso_vivo"), delta_bom="up"), md=3),
            dbc.Col(card_kpi("Rendimento Industrial",
                             _fmt_pct(k.get("rend_industrial_pct", 0)),
                             f"Carcaça: {_fmt_pct(k.get('rend_carcaca_pct', 0))}",
                             icone="bi-graph-up-arrow", cor=CORES["destaque"],
                             delta_pct=_dv("rend_industrial"), delta_bom="up"), md=3),
            dbc.Col(card_kpi("Taxa de Condenação",
                             _fmt_pct(k.get("taxa_condena_pct", 0)),
                             "Menos é melhor",
                             icone="bi-exclamation-triangle-fill", cor=CORES["alerta"],
                             delta_pct=_dv("taxa_condena"), delta_bom="down"), md=3),
        ]

        banner = _banner_alertas(gerar_alertas(f, mom))

        # Série temporal com PROJEÇÃO
        st = serie_temporal(f, freq="ME") if not f.empty else pd.DataFrame()
        fig_temp = go.Figure()
        if not st.empty and len(st) >= 3:
            st_idx = st.set_index("Data")[metrica]
            proj = prever(st_idx, n_meses=3)
            hist = proj[proj["tipo"] == "histórico"]
            futu = proj[proj["tipo"] == "projeção"]

            fig_temp.add_trace(go.Scatter(
                x=hist["Data"], y=hist["valor"], mode="lines+markers",
                name="Histórico",
                line=dict(color=CORES["primaria"], width=3, shape="spline"),
                marker=dict(size=8, line=dict(color="white", width=2)),
                hovertemplate="<b>%{x|%b %Y}</b><br>%{y:,.0f}<extra></extra>"))

            if not futu.empty:
                fig_temp.add_trace(go.Scatter(
                    x=[hist["Data"].iloc[-1]] + list(futu["Data"]),
                    y=[hist["valor"].iloc[-1]] + list(futu["valor"]),
                    mode="lines+markers", name="Projeção",
                    line=dict(color=CORES["destaque"], width=3, dash="dot", shape="spline"),
                    marker=dict(size=8, symbol="diamond",
                                line=dict(color="white", width=2)),
                    hovertemplate="<b>%{x|%b %Y}</b><br>Proj: %{y:,.0f}<extra></extra>"))
                fig_temp.add_trace(go.Scatter(
                    x=list(futu["Data"]) + list(futu["Data"][::-1]),
                    y=list(futu["upper"]) + list(futu["lower"][::-1]),
                    fill="toself", fillcolor="rgba(255,179,0,0.15)",
                    line=dict(width=0), name="Intervalo ±1σ",
                    hoverinfo="skip"))
        fig_temp.update_layout(
            template="plotly_white", height=360,
            margin=dict(l=10, r=10, t=10, b=20),
            yaxis_title=metrica.replace("_", " "),
            font=dict(family="Inter, sans-serif", size=12, color="#1A1A1A"),
            xaxis=dict(showgrid=False, showline=True, linecolor="#E5E7EB"),
            yaxis=dict(gridcolor="#F0F2F0", zeroline=False),
            legend=dict(orientation="h", y=-0.18, font=dict(size=12)),
            hoverlabel=dict(bgcolor="white", font_family="Inter",
                            bordercolor="#E5E7EB"),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")

        # Ranking
        rank = kpis_por_parceiro(f) if not f.empty else pd.DataFrame()
        fig_rank = go.Figure()
        if not rank.empty:
            fig_rank.add_trace(go.Bar(
                x=rank["Rend_Carcaca_%"], y=rank["Parceiro"],
                orientation="h",
                marker=dict(
                    color=rank["Rend_Carcaca_%"],
                    colorscale=[[0, "#A5D6A7"], [1, "#1B5E20"]],
                    line=dict(width=0)),
                text=[f"<b>{v:.2f}%</b>" for v in rank["Rend_Carcaca_%"]],
                textposition="inside", insidetextanchor="end",
                textfont=dict(color="white", size=12),
                hovertemplate="<b>%{y}</b><br>Rend: %{x:.2f}%<extra></extra>"))
        fig_rank.update_layout(template="plotly_white", height=300,
                               margin=dict(l=10, r=10, t=10, b=30),
                               xaxis_title="Rendimento de Carcaça (%)",
                               font=dict(family="Inter, sans-serif", size=12),
                               xaxis=dict(showgrid=False, range=[74, 78]),
                               yaxis=dict(showgrid=False),
                               plot_bgcolor="rgba(0,0,0,0)",
                               paper_bgcolor="rgba(0,0,0,0)",
                               hoverlabel=dict(bgcolor="white",
                                               font_family="Inter",
                                               bordercolor="#E5E7EB"))

        # Mix família (recalcula com filtros de família/parceiro/data)
        prod = dfs["Producao"].copy()
        prod["Data"] = pd.to_datetime(prod["Data"], dayfirst=True, errors="coerce")
        prod = prod[(prod["Data"] >= start) & (prod["Data"] <= end)
                    & (prod["Parceiro"].isin(parceiros or []))
                    & (prod["Família"].isin(familias or []))]
        mx = mix_familia(prod) if not prod.empty else pd.DataFrame()
        fig_mix = go.Figure()
        if not mx.empty:
            fig_mix.add_trace(go.Pie(
                labels=mx["Família"], values=mx["Total_Kg"],
                hole=0.62,
                marker=dict(colors=["#1B5E20", "#2E7D32", "#43A047",
                                    "#66BB6A", "#A5D6A7", "#C8E6C9", "#E8F5E9"],
                            line=dict(color="white", width=2)),
                textinfo="label+percent", textfont=dict(size=11),
                hovertemplate="<b>%{label}</b><br>%{value:,.0f} kg<br>%{percent}<extra></extra>"))
        fig_mix.update_layout(template="plotly_white", height=300,
                              margin=dict(l=10, r=10, t=10, b=10),
                              font=dict(family="Inter, sans-serif", size=12),
                              showlegend=False,
                              plot_bgcolor="rgba(0,0,0,0)",
                              paper_bgcolor="rgba(0,0,0,0)",
                              hoverlabel=dict(bgcolor="white",
                                              font_family="Inter",
                                              bordercolor="#E5E7EB"))

        # Drilldown
        if not prod.empty:
            sku = (prod.groupby(["SKU", "Nome_Produto", "Família"], as_index=False)
                       .agg(Total_Kg=("Total_Produzido", "sum"))
                       .sort_values("Total_Kg", ascending=False).head(20))
            sku["Total_Kg"] = sku["Total_Kg"].map(lambda v: f"{v:,.0f}".replace(",", "."))
            tabela = dash_table.DataTable(
                data=sku.to_dict("records"),
                columns=[{"name": c, "id": c} for c in sku.columns],
                style_cell={"fontFamily": "Inter, sans-serif", "fontSize": "13px",
                            "padding": "8px", "textAlign": "left"},
                style_header={"backgroundColor": CORES["primaria"], "color": "white",
                              "fontWeight": "bold"},
                style_data_conditional=[{"if": {"row_index": "odd"},
                                         "backgroundColor": "#FAFAFA"}],
                page_size=10)
        else:
            tabela = html.Div("Sem dados para o filtro selecionado.",
                              style={"padding": "20px", "color": CORES["texto_fraco"]})

        periodo_txt = (f"📅 {pd.to_datetime(start).strftime('%d/%m/%Y')} → "
                       f"{pd.to_datetime(end).strftime('%d/%m/%Y')}")

        return cards, banner, fig_temp, fig_rank, fig_mix, tabela, periodo_txt
