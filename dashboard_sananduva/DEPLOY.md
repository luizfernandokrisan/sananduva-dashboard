# Deploy — Dashboard Sananduva

Guia para colocar o dashboard online com autenticação funcionando.

---

## OPÇÃO 1 · Render (recomendado — free tier)

**Tempo estimado: 8 minutos.**

### Passo 1 — Subir código no GitHub
```bash
cd dashboard_sananduva
git init
git add .
git commit -m "Dashboard Sananduva — versão inicial"
gh repo create sananduva-dashboard --private --source=. --push
# ou pelo site do GitHub, depois:
# git remote add origin https://github.com/SEU_USUARIO/sananduva-dashboard.git
# git branch -M main && git push -u origin main
```

### Passo 2 — Conectar Render ao repositório
1. Acesse https://dashboard.render.com → **New + → Blueprint**
2. Conecte sua conta GitHub e selecione o repositório `sananduva-dashboard`
3. Render detecta o `render.yaml` automaticamente e mostra a config
4. Clique **Apply** — o deploy começa

### Passo 3 — Aguardar build
- Build leva ~4 minutos (instala deps, gera SQLite, cria usuários demo)
- URL final: `https://dashboard-sananduva.onrender.com` (ou similar)

### Passo 4 — Acessar
- Abra a URL → será redirecionado pra `/login`
- Use `luiz` / `luiz@2026` (ou os outros usuários demo)

### ⚠ Limitações do tier free
- **App "dorme" após 15 min sem tráfego**: primeira request depois disso leva ~30s
- **Filesystem efêmero**: cada deploy recria o `sananduva.db` do zero (Excel é commitado, então dados ficam OK; mas usuários voltam aos demo)
- **Sem custom domain** (só `*.onrender.com`)
- **750 hrs/mês** de uptime

---

## OPÇÃO 2 · Railway

**Tempo: 6 minutos. Tem $5 grátis iniciais, depois ~$5/mês.**

```bash
npm install -g @railway/cli
railway login
cd dashboard_sananduva
railway init
railway up
railway variables --set SANANDUVA_SECRET=$(openssl rand -hex 32)
railway variables --set DASH_DEBUG=false
railway domain   # gera URL pública
```

Railway lê o `Procfile` automaticamente. O bridge SQLite + setup_auth precisam
ser rodados manualmente uma vez:
```bash
railway run python src/db/sqlite_bridge.py
railway run python src/db/setup_auth.py
```

---

## OPÇÃO 3 · Fly.io (mais técnico, free com cartão)

Requer `flyctl`. Inclui volume persistente grátis (3 GB) — **a única
opção free com SQLite persistente de verdade.**

```bash
brew install flyctl   # ou curl https://fly.io/install.sh | sh
flyctl auth signup
cd dashboard_sananduva
flyctl launch --name dashboard-sananduva --region gru --no-deploy
flyctl volumes create sananduva_data --region gru --size 1
# editar fly.toml: adicionar [mounts] source = "sananduva_data" destination = "/data"
flyctl secrets set SANANDUVA_SECRET=$(openssl rand -hex 32)
flyctl deploy
```

---

## Migração futura: SQLite → PostgreSQL (eliminar limitação efêmera)

Quando bater na limitação do free tier do Render:

1. No Render dashboard → **New + → PostgreSQL** (free tier 90 dias)
2. Copiar `DATABASE_URL` para os env vars do app
3. Trocar `src/data_loader.py` `_from_sqlite()` por SQLAlchemy + psycopg2
4. Trocar `src/auth.py` `_conexao()` por mesma camada
5. Reaplicar `schema.sql` no Postgres

O código já está modular pra essa troca — `DataLoader(source='postgres')`.

---

## Variáveis de ambiente importantes

| Var | Default | Quando trocar |
|---|---|---|
| `PORT` | 8050 | Plataforma define automaticamente |
| `SANANDUVA_SECRET` | string demo | **OBRIGATÓRIO trocar em prod** (32+ chars) |
| `DASH_DEBUG` | `true` (dev) | Setar `false` em produção |

---

## Pós-deploy: checklist

- [ ] Acessei `/login` e fui autenticado
- [ ] Dashboard carrega após login
- [ ] Botão "Sair" no header funciona
- [ ] Troquei senhas demo (`admin@2026` etc.) por senhas reais
- [ ] Setei `SANANDUVA_SECRET` com valor aleatório (não o default)
- [ ] Compartilhei URL + credenciais com diretoria via canal seguro
