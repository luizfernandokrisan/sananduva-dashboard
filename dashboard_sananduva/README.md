# Dashboard Sananduva — Rendimento de Carcaças Suínas

Dashboard operacional para visão de **Diretoria, Gerência e Coordenação Industrial**.

## Estrutura

```
dashboard_sananduva/
├── data/
│   ├── Base_DB_Sananduva.xlsx     # base de origem (Fase 1)
│   └── sananduva.db               # SQLite gerado pelo bridge (Fase 2)
├── src/
│   ├── config.py                  # paths, schema, paleta
│   ├── data_loader.py             # abstrai Excel / SQLite / Oracle
│   ├── transformations.py         # consolida 3 tabelas em 1 fato
│   ├── kpis.py                    # KPIs executivos e por parceiro
│   └── db/
│       ├── schema.sql             # DDL espelho do futuro Oracle
│       └── sqlite_bridge.py       # migração Excel → SQLite
├── app/
│   ├── app.py                     # entrypoint Dash
│   ├── layout.py                  # estrutura visual (header, filtros, cards)
│   ├── callbacks.py               # interatividade
│   └── components/
│       └── kpi_cards.py           # cards reutilizáveis
└── requirements.txt
```

## Como rodar

```bash
# 1) Setup
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2) (opcional) Gerar SQLite a partir do Excel
python src/db/sqlite_bridge.py

# 3) Criar usuários iniciais (UMA vez)
python src/db/setup_auth.py

# 4) Subir o dashboard
python app/app.py
# → http://127.0.0.1:8050/login
```

## Usuários demo (TROCAR EM PRODUÇÃO)

| Usuário | Senha | Role |
|---|---|---|
| admin   | admin@2026   | admin |
| diretor | diretor@2026 | diretor |
| luiz    | luiz@2026    | analista |

Para trocar senhas / criar usuários, use as funções de `src/auth.py`:
```python
from auth import criar_usuario
criar_usuario("novo.usuario", "Nome Completo", "Senha@Forte", role="diretor")
```

⚠ **Em produção:** definir variável `SANANDUVA_SECRET` (32+ chars aleatórios)
e migrar para SSO corporativo (Azure AD / Google Workspace) via OIDC.

## Fluxo macro do negócio (refletido no fato consolidado)

```
Suíno pesado  →  Abate  →  Condenação (descontos)  →  Produção
   (PV, kg)     (PCQ)         (Peso_Condena)        (Total_Produzido)
```

## KPIs principais

| KPI | Fórmula |
|---|---|
| Cabeças abatidas | Σ Quantidade |
| Peso vivo total | Σ Peso_Vivo_Kg |
| Rendimento de Carcaça | Σ PCQ / Σ PV × 100 |
| Rendimento Industrial | Σ Produzido / Σ PV × 100 |
| Taxa de Condenação | Σ Condena / Σ PV × 100 |
| Peso médio | Σ PV / Σ Cabeças |

## Roadmap

- [x] **Fase 1** — Base Excel
- [x] **Fase 2** — Pipeline de dados (loader/transforms/kpis) + SQLite
- [x] **Fase 3** — Dashboard Dash operacional
- [ ] **Fase 4** — Migração para Oracle
- [ ] **Fase 5** — Deploy online (Render / Railway / interno)
- [ ] **Fase 6** — Autenticação corporativa
