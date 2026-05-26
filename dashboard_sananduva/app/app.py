"""Entrypoint do Dashboard Sananduva — agora com Flask-Login.
   Rotas:
     GET  /login   → página de login (Flask)
     POST /login   → valida credenciais
     GET  /logout  → encerra sessão
     GET  /        → dashboard Dash (protegido)
"""
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

import dash
import dash_bootstrap_components as dbc
from flask import Flask, render_template_string, request, redirect, session
from flask_login import (LoginManager, login_user, logout_user,
                         current_user, login_required)

from data_loader import DataLoader
from transformations import consolidar
from auth import autenticar, buscar_por_id, garantir_tabela
from layout import build_layout
from callbacks import register_callbacks
from auth_pages import LOGIN_HTML

# ============================================================
# 1) Carrega dados (uma vez na inicialização)
# ============================================================
dfs = DataLoader().load()
fato = consolidar(dfs)
garantir_tabela()

# ============================================================
# 2) Servidor Flask + Flask-Login
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
        username = request.form.get("username", "").strip()
        senha    = request.form.get("password", "")
        user = autenticar(username, senha)
        if user:
            login_user(user, remember=True)
            return redirect("/")
        erro = "Usuário ou senha incorretos."
    return render_template_string(LOGIN_HTML, error=erro)


@server.route("/logout")
@login_required
def logout_route():
    logout_user()
    return redirect("/login")


# Guarda TODAS as rotas: bloqueia se não autenticado, exceto as públicas
@server.before_request
def _exige_login():
    publicas = ("/login", "/logout")
    eh_asset = request.path.startswith(("/assets/", "/_dash-", "/_favicon"))
    if not current_user.is_authenticated and request.path not in publicas and not eh_asset:
        return redirect("/login")


# ============================================================
# 3) App Dash (montado em /)
# ============================================================
app = dash.Dash(
    __name__,
    server=server,
    external_stylesheets=[dbc.themes.FLATLY, dbc.icons.BOOTSTRAP],
    title="Dashboard Sananduva",
    suppress_callback_exceptions=True,
    assets_folder="../assets",
)

app.layout = build_layout(fato, dfs)
register_callbacks(app, fato, dfs)


if __name__ == "__main__":
    port  = int(os.environ.get("PORT", 8050))
    debug = os.environ.get("DASH_DEBUG", "true").lower() == "true"
    app.run(debug=debug, host="0.0.0.0", port=port)
