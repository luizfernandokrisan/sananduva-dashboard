"""Entrypoint do Dashboard Sananduva — multi-página com Flask-Login.

Rotas:
  GET  /login       → página de login
  GET  /logout      → encerra sessão
  GET  /            → dashboard operacional (protegido)
  GET  /analise     → análise estatística avançada (protegido)
"""
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
from flask import Flask, render_template_string, request, redirect
from flask_login import (LoginManager, login_user, logout_user,
                         current_user, login_required)

from data_loader import DataLoader
from transformations import consolidar
from auth import autenticar, buscar_por_id, garantir_tabela
from layout import build_layout
from callbacks import register_callbacks
from analise import build_layout_analise
from callbacks_analise import register_callbacks_analise
from auth_pages import LOGIN_HTML

# ============================================================
# 1) Dados
# ============================================================
dfs = DataLoader().load()
fato = consolidar(dfs)
garantir_tabela()

# ============================================================
# 2) Flask + Auth
# ============================================================
server = Flask(__name__)
server.config["SECRET_KEY"] = os.environ.get("SANANDUVA_SECRET",
                                              "troque-isto-em-producao-32chars!")

login_manager = LoginManager()
login_manager.init_app(server)
login_manager.login_view = "/login"


@login_manager.user_loader
def _load_user(user_id):
    return buscar_por_id(int(user_id))


@server.route("/login", methods=["GET", "POST"])
def login_route():
    if current_user.is_authenticated:
        return redirect("/")
    erro = None
    if request.method == "POST":
        u = autenticar(request.form.get("username", "").strip(),
                       request.form.get("password", ""))
        if u:
            login_user(u, remember=True)
            return redirect("/")
        erro = "Usuário ou senha incorretos."
    return render_template_string(LOGIN_HTML, error=erro)


@server.route("/logout")
@login_required
def logout_route():
    logout_user()
    return redirect("/login")


@server.before_request
def _exige_login():
    publicas = ("/login", "/logout")
    eh_asset = request.path.startswith(("/assets/", "/_dash-", "/_favicon"))
    if not current_user.is_authenticated and request.path not in publicas and not eh_asset:
        return redirect("/login")


# ============================================================
# 3) App Dash multi-página
# ============================================================
app = dash.Dash(
    __name__,
    server=server,
    external_stylesheets=[dbc.themes.FLATLY, dbc.icons.BOOTSTRAP],
    title="Dashboard Sananduva",
    suppress_callback_exceptions=True,
    assets_folder="../assets",
)

# Layouts pré-construídos (carregam uma vez)
LAYOUT_OPERACIONAL = build_layout(fato, dfs)
LAYOUT_ANALISE = build_layout_analise(fato, dfs)

app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    html.Div(id="conteudo-pagina"),
])


@app.callback(Output("conteudo-pagina", "children"),
              Input("url", "pathname"))
def _roteador(pathname):
    if pathname == "/analise":
        return LAYOUT_ANALISE
    return LAYOUT_OPERACIONAL


# Registra todos os callbacks de ambas as páginas
register_callbacks(app, fato, dfs)
register_callbacks_analise(app, fato, dfs)


if __name__ == "__main__":
    port  = int(os.environ.get("PORT", 8050))
    debug = os.environ.get("DASH_DEBUG", "true").lower() == "true"
    app.run(debug=debug, host="0.0.0.0", port=port)
