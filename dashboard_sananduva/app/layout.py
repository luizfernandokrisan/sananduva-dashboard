"""Layout do dashboard — visão operacional com filtros e drilldown.
   Estilo aplicado via assets/custom.css (Inter + Space Grotesk)."""
import pandas as pd
from dash import dcc, html
import dash_bootstrap_components as dbc

from config import PARCEIROS


def _sidebar_filtros(fato: pd.DataFrame, dfs: dict) -> html.Div:
    return html.Div(
        className="sidebar card",
        style={"padding": "22px"},
        children=[
            html.Div(style={"display": "flex", "alignItems": "center",
                            "gap": "8px", "marginBottom": "4px"}, children=[
                html.I(className="bi bi-funnel-fill",
                       style={"color": "var(--color-primary)", "fontSize": "16px"}),
                html.H5("Filtros", style={"margin": 0,
                                          "color": "var(--color-primary)"}),
            ]),
            html.Hr(style={"margin": "12px 0 20px", "opacity": 0.2}),

            html.Label("Período"),
            dcc.DatePickerRange(
                id="filtro-periodo",
                min_date_allowed=fato["Data"].min(),
                max_date_allowed=fato["Data"].max(),
                start_date=fato["Data"].min(),
                end_date=fato["Data"].max(),
                display_format="DD/MM/YYYY",
                style={"width": "100%", "marginBottom": "20px"},
            ),

            html.Label("Parceiros"),
            dcc.Dropdown(
                id="filtro-parceiro",
                options=[{"label": p, "value": p} for p in PARCEIROS],
                value=PARCEIROS, multi=True,
                style={"marginBottom": "20px"},
            ),

            html.Label("Tipo de Suíno"),
            dcc.Dropdown(
                id="filtro-tipo",
                options=[{"label": t, "value": t}
                         for t in dfs["Abate"]["Tipo_Suino"].unique()],
                value=list(dfs["Abate"]["Tipo_Suino"].unique()),
                multi=True,
                style={"marginBottom": "20px"},
            ),

            html.Label("Família de Produto"),
            dcc.Dropdown(
                id="filtro-familia",
                options=[{"label": f, "value": f}
                         for f in sorted(dfs["Producao"]["Família"].unique())],
                value=sorted(dfs["Producao"]["Família"].unique()),
                multi=True,
            ),
        ],
    )


def _header() -> html.Div:
    return html.Div(
        className="app-header",
        children=[
            dbc.Row(align="center", children=[
                dbc.Col([
                    html.Div(style={"display": "flex", "alignItems": "center",
                                    "gap": "10px"}, children=[
                        html.I(className="bi bi-pie-chart-fill",
                               style={"color": "#FFFFFF", "fontSize": "28px"}),
                        html.Div([
                            html.H2("Dashboard Sananduva",
                                    style={"margin": 0, "fontSize": "22px"}),
                            html.Small(["Rendimento de Carcaças Suínas · ",
                                        html.Span(className="live-dot"),
                                        "Atualizado em tempo real"]),
                        ]),
                    ]),
                ], width=12, md=7),

                dbc.Col(width=12, md=5, children=[
                    html.Div(style={"display": "flex", "alignItems": "center",
                                    "justifyContent": "flex-end", "gap": "16px",
                                    "flexWrap": "wrap"}, children=[
                        html.Div(id="header-periodo",
                                 style={"color": "#FFFFFF", "fontSize": "13px",
                                        "opacity": 0.9}),
                        html.Div(id="user-badge", className="user-badge"),
                    ]),
                ]),
            ]),
        ],
    )


def build_layout(fato: pd.DataFrame, dfs: dict) -> html.Div:
    return html.Div(
        style={"minHeight": "100vh"},
        children=[
            _header(),
            dbc.Container(fluid=True, style={"padding": "28px 32px 40px"},
                          children=[
                html.Div(id="banner-alertas", className="mb-4"),

                dbc.Row([
                    dbc.Col(_sidebar_filtros(fato, dfs), width=12, lg=3),

                    dbc.Col(width=12, lg=9, children=[
                        dbc.Row(id="row-cards", className="g-3 mb-4"),

                        dbc.Card(className="mb-3", body=True, children=[
                            html.Div(style={"display": "flex",
                                            "justifyContent": "space-between",
                                            "alignItems": "center",
                                            "marginBottom": "8px",
                                            "flexWrap": "wrap", "gap": "8px"},
                                     children=[
                                html.H5("Evolução temporal + Projeção 3 meses"),
                                dcc.RadioItems(
                                    id="seletor-metrica-temporal",
                                    options=[
                                        {"label": "  Peso Vivo  ", "value": "Peso_Vivo_Kg"},
                                        {"label": "  Produzido  ", "value": "Produzido_Kg"},
                                        {"label": "  Rend. Carcaça  ", "value": "Rend_Carcaca_%"},
                                    ],
                                    value="Peso_Vivo_Kg",
                                    inline=True,
                                    className="dash-radio-items",
                                ),
                            ]),
                            dcc.Loading(
                                dcc.Graph(id="grafico-temporal",
                                          config={"displayModeBar": False}),
                                type="circle",
                                color="var(--color-primary)",
                            ),
                        ]),

                        dbc.Row(className="g-3 mb-3", children=[
                            dbc.Col(dbc.Card(body=True, children=[
                                html.H5("Ranking de Parceiros",
                                        style={"marginBottom": "12px"}),
                                dcc.Loading(
                                    dcc.Graph(id="grafico-ranking",
                                              config={"displayModeBar": False}),
                                    type="circle",
                                    color="var(--color-primary)"),
                            ]), md=6),
                            dbc.Col(dbc.Card(body=True, children=[
                                html.H5("Mix de Produção · Família",
                                        style={"marginBottom": "12px"}),
                                dcc.Loading(
                                    dcc.Graph(id="grafico-mix",
                                              config={"displayModeBar": False}),
                                    type="circle",
                                    color="var(--color-primary)"),
                            ]), md=6),
                        ]),

                        dbc.Card(body=True, children=[
                            html.Div(style={"display": "flex",
                                            "justifyContent": "space-between",
                                            "alignItems": "center",
                                            "marginBottom": "12px"}, children=[
                                html.H5("Drilldown · Top 20 SKUs"),
                                html.Small("Clique no header para ordenar",
                                           style={"color": "var(--color-text-soft)",
                                                  "fontSize": "11px"}),
                            ]),
                            html.Div(id="tabela-drilldown"),
                        ]),
                    ]),
                ]),
            ]),
        ],
    )
