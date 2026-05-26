"""Página de Análise Estatística Avançada.

5 análises (Irgang, Dutra Jr, Barbosa et al.):
1. Curva Peso × Rendimento (linear + quadrático, peso ótimo)
2. Matriz de Correlação
3. PCA 2D
4. Regressão Múltipla
5. Distribuição Estatística
"""
from dash import dcc, html
import dash_bootstrap_components as dbc

from config import CORES


def _card_analise(titulo: str, subtitulo: str, conteudo, icone: str = "bi-graph-up") -> dbc.Card:
    return dbc.Card(className="mb-4", body=True, children=[
        html.Div(style={"display": "flex", "alignItems": "center",
                        "gap": "12px", "marginBottom": "8px"}, children=[
            html.Div(className="kpi-icon",
                     style={"background": f"{CORES['primaria']}15",
                            "color": CORES["primaria"]},
                     children=html.I(className=f"bi {icone}")),
            html.Div([
                html.H5(titulo, style={"margin": 0}),
                html.Small(subtitulo, style={"color": CORES["texto_fraco"]}),
            ]),
        ]),
        html.Hr(style={"margin": "8px 0 16px", "opacity": 0.15}),
        conteudo,
    ])


def _header_analise() -> html.Div:
    return html.Div(
        className="app-header",
        children=[
            dbc.Row(align="center", children=[
                dbc.Col([
                    html.Div(style={"display": "flex", "alignItems": "center",
                                    "gap": "10px"}, children=[
                        html.I(className="bi bi-bezier2",
                               style={"color": "#FFFFFF", "fontSize": "28px"}),
                        html.Div([
                            html.H2("Análise Estatística Avançada",
                                    style={"margin": 0, "fontSize": "22px"}),
                            html.Small(["Regressões · PCA · Peso Ótimo · ",
                                        html.A("← Voltar ao Dashboard",
                                               href="/",
                                               style={"color": "#FFE082",
                                                      "textDecoration": "none"})]),
                        ]),
                    ]),
                ], width=12, md=8),
                dbc.Col(width=12, md=4, children=[
                    html.Div(style={"display": "flex", "alignItems": "center",
                                    "justifyContent": "flex-end", "gap": "12px"},
                             children=[
                        html.Div(id="user-badge-analise", className="user-badge"),
                    ]),
                ]),
            ]),
        ],
    )


def build_layout_analise(fato, dfs):
    return html.Div(
        style={"minHeight": "100vh"},
        children=[
            _header_analise(),
            dbc.Container(fluid=True, style={"padding": "28px 32px 40px",
                                              "maxWidth": "1400px"}, children=[
                # Banner de contexto
                dbc.Alert([
                    html.I(className="bi bi-info-circle-fill",
                           style={"marginRight": "8px"}),
                    html.Strong("Base teórica: "),
                    "Irgang & Protas (1986) · Dutra Jr. et al. (2001) · ",
                    "Barbosa et al. (2005) · Oliveira et al. (2015). ",
                    html.Em("Dados de demonstração — modelos serão revalidados com dados reais.")
                ], color="info", style={"fontSize": "13px",
                                         "background": "#E3F2FD",
                                         "borderColor": "#90CAF9",
                                         "color": "#0D47A1"}),

                # Filtros mínimos no topo (período + parceiros)
                dbc.Card(className="mb-4", body=True, children=[
                    dbc.Row(align="end", children=[
                        dbc.Col([
                            html.Label("Período de análise"),
                            dcc.DatePickerRange(
                                id="ana-periodo",
                                min_date_allowed=fato["Data"].min(),
                                max_date_allowed=fato["Data"].max(),
                                start_date=fato["Data"].min(),
                                end_date=fato["Data"].max(),
                                display_format="DD/MM/YYYY",
                                style={"width": "100%"},
                            ),
                        ], md=4),
                        dbc.Col([
                            html.Label("Parceiros incluídos"),
                            dcc.Dropdown(
                                id="ana-parceiros",
                                options=[{"label": p, "value": p}
                                         for p in fato["Parceiro"].unique()],
                                value=list(fato["Parceiro"].unique()),
                                multi=True,
                            ),
                        ], md=8),
                    ]),
                ]),

                # ============ ANÁLISE 1: PESO ÓTIMO DE ABATE ============
                _card_analise(
                    "1 · Curva Peso × Rendimento de Carcaça",
                    "Identifica o peso ótimo de abate via regressão polinomial",
                    icone="bi-bezier",
                    conteudo=html.Div([
                        dcc.Loading(dcc.Graph(id="ana-grafico-pesootimo",
                                              config={"displayModeBar": False}),
                                    color=CORES["primaria"]),
                        dbc.Row(className="mt-3 g-3", children=[
                            dbc.Col(html.Div(id="ana-equacao-linear",
                                             className="formula-box"), md=6),
                            dbc.Col(html.Div(id="ana-equacao-quadratica",
                                             className="formula-box"), md=6),
                        ]),
                        html.Div(id="ana-interpretacao-pesootimo",
                                 className="interpretacao-box mt-3"),
                    ]),
                ),

                # ============ ANÁLISE 2: MATRIZ DE CORRELAÇÃO ============
                _card_analise(
                    "2 · Matriz de Correlação",
                    "Quais variáveis se movem juntas? (Pearson)",
                    icone="bi-grid-3x3",
                    conteudo=html.Div([
                        dcc.Loading(dcc.Graph(id="ana-grafico-correlacao",
                                              config={"displayModeBar": False}),
                                    color=CORES["primaria"]),
                        html.Div(id="ana-interpretacao-correlacao",
                                 className="interpretacao-box mt-3"),
                    ]),
                ),

                # ============ ANÁLISE 3: PCA ============
                _card_analise(
                    "3 · Análise de Componentes Principais (PCA)",
                    "Redução dimensional — Barbosa et al. (2005) aplicado à sua operação",
                    icone="bi-scatter-chart",
                    conteudo=dbc.Row([
                        dbc.Col(dcc.Loading(
                            dcc.Graph(id="ana-grafico-pca",
                                      config={"displayModeBar": False}),
                            color=CORES["primaria"]), md=7),
                        dbc.Col([
                            html.Div(id="ana-tabela-variancia"),
                            html.Div(id="ana-interpretacao-pca",
                                     className="interpretacao-box mt-3"),
                        ], md=5),
                    ]),
                ),

                # ============ ANÁLISE 4: REGRESSÃO MÚLTIPLA ============
                _card_analise(
                    "4 · Regressão Múltipla — Drivers do Rendimento Industrial",
                    "Quais variáveis explicam o aproveitamento da produção?",
                    icone="bi-diagram-3",
                    conteudo=html.Div([
                        html.Div(id="ana-tabela-multipla"),
                        dcc.Loading(dcc.Graph(id="ana-grafico-residuos",
                                              config={"displayModeBar": False}),
                                    color=CORES["primaria"]),
                        html.Div(id="ana-interpretacao-multipla",
                                 className="interpretacao-box mt-3"),
                    ]),
                ),

                # ============ ANÁLISE 5: DISTRIBUIÇÃO ============
                _card_analise(
                    "5 · Distribuição do Rendimento por Parceiro",
                    "Variabilidade, outliers e teste de normalidade",
                    icone="bi-bar-chart-line",
                    conteudo=html.Div([
                        dcc.RadioItems(
                            id="ana-metrica-dist",
                            options=[
                                {"label": "  Rend. Carcaça (%)  ", "value": "Rend_Carcaca_%"},
                                {"label": "  Rend. Industrial (%)  ", "value": "Rend_Industrial_%"},
                                {"label": "  Peso Médio (kg)  ", "value": "Peso_Medio_Kg"},
                            ],
                            value="Rend_Carcaca_%",
                            inline=True, className="dash-radio-items mb-3",
                        ),
                        dcc.Loading(dcc.Graph(id="ana-grafico-dist",
                                              config={"displayModeBar": False}),
                                    color=CORES["primaria"]),
                        html.Div(id="ana-tabela-descritiva", className="mt-3"),
                    ]),
                ),

                # Rodapé com referências
                dbc.Card(body=True, className="mt-4",
                         style={"background": "#FAFBFA", "fontSize": "11px"},
                         children=[
                    html.Strong("📚 Referências utilizadas:"),
                    html.Ul([
                        html.Li("Irgang, R. & Protas, J.F.S. (1986). Peso ótimo de abate de suínos. "
                                "II. Resultados de carcaça. Pesq. agropec. bras. 21(12):1337-1345."),
                        html.Li("Dutra Jr., W.M. et al. (2001). Estimativa de rendimentos de cortes "
                                "comerciais e de tecidos de suínos em diferentes pesos de abate pela "
                                "técnica de ultra-sonografia em tempo real."),
                        html.Li("Barbosa et al. (2005). Avaliação de características de carcaça de "
                                "suínos utilizando análise dos componentes principais. R. Bras. "
                                "Zootec. 34(6):2209-2217."),
                        html.Li("Oliveira et al. (2015) via Embrapa Suínos e Aves: ponto ótimo "
                                "econômico de abate ~135 kg de peso vivo."),
                    ], style={"marginTop": "6px", "marginBottom": 0}),
                ]),
            ]),
        ],
    )
