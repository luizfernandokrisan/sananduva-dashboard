"""Card KPI — visual moderno, estilo ECOFRIGO.
   Estilização pesada delegada ao assets/custom.css (.kpi-card, .kpi-value, etc.)."""
from dash import html
import dash_bootstrap_components as dbc


def card_kpi(titulo: str, valor: str, subtitulo: str = "",
             icone: str = "bi-bar-chart-fill", cor: str = "#1B5E20",
             delta_pct: float = None, delta_bom: str = "up") -> dbc.Card:
    """delta_bom='up' → variação positiva é verde; 'down' → variação negativa é verde."""

    # Delta MoM
    delta_node = None
    if delta_pct is not None:
        positivo = delta_pct > 0
        eh_bom = (positivo and delta_bom == "up") or (not positivo and delta_bom == "down")
        classe = "kpi-delta kpi-delta-up" if eh_bom else "kpi-delta kpi-delta-down"
        seta = "▲" if positivo else ("▼" if delta_pct < 0 else "▬")
        delta_node = html.Span(f"{seta} {abs(delta_pct):.1f}%",
                               className=classe)

    icone_box = html.Div(
        className="kpi-icon",
        style={"background": f"{cor}15", "color": cor},
        children=html.I(className=f"bi {icone}"),
    )

    return dbc.Card(
        className="kpi-card",
        style={"color": cor},   # passa cor via currentColor pra ::before
        body=True,
        children=[
            html.Div(style={"display": "flex", "alignItems": "center",
                            "gap": "14px"}, children=[
                icone_box,
                html.Div(style={"flex": 1, "minWidth": 0}, children=[
                    html.Div(titulo, className="kpi-label"),
                    html.Div(valor, className="kpi-value"),
                    html.Div(style={"display": "flex", "alignItems": "center",
                                    "gap": "4px", "flexWrap": "wrap"}, children=[
                        html.Span(subtitulo, className="kpi-sub"),
                        delta_node if delta_node else html.Span(),
                    ]),
                ]),
            ]),
        ],
    )
