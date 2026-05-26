"""HTML da página de login. Mantém a mesma identidade visual do dashboard
   (Inter + paleta verde). Sem framework JS — só Flask + form clássico."""

LOGIN_HTML = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login · Dashboard Sananduva</title>
    <link rel="stylesheet"
          href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@500;600;700&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; -webkit-font-smoothing: antialiased; }
        :root {
            --color-primary: #1B5E20;
            --color-primary-dark: #0E3D11;
            --color-secondary: #2E7D32;
            --color-accent: #FFB300;
            --color-danger: #C62828;
            --color-text: #1A1A1A;
            --color-muted: #6B7280;
            --color-border: #E5E7EB;
        }
        body {
            font-family: 'Inter', system-ui, sans-serif;
            min-height: 100vh;
            display: flex; align-items: center; justify-content: center;
            background:
                radial-gradient(circle at 20% 30%, rgba(46,125,50,0.10) 0%, transparent 50%),
                radial-gradient(circle at 80% 70%, rgba(27,94,32,0.12) 0%, transparent 50%),
                linear-gradient(135deg, #F4F6F4 0%, #E8F0E8 100%);
            color: var(--color-text);
            padding: 20px;
        }
        .login-card {
            background: white;
            border-radius: 18px;
            padding: 40px 36px;
            width: 100%; max-width: 420px;
            box-shadow:
                0 16px 40px rgba(15,23,19,0.08),
                0 4px 12px rgba(15,23,19,0.04);
            position: relative;
            overflow: hidden;
            animation: slideIn 500ms cubic-bezier(0.16, 1, 0.3, 1);
        }
        .login-card::before {
            content: '';
            position: absolute; left: 0; top: 0; right: 0;
            height: 4px;
            background: linear-gradient(90deg, var(--color-accent) 0%,
                        var(--color-secondary) 50%, var(--color-primary) 100%);
        }
        @keyframes slideIn {
            from { opacity: 0; transform: translateY(20px); }
            to   { opacity: 1; transform: translateY(0); }
        }
        .brand {
            display: flex; align-items: center; gap: 12px;
            margin-bottom: 28px;
        }
        .brand-icon {
            width: 48px; height: 48px;
            border-radius: 14px;
            background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%);
            color: white;
            display: flex; align-items: center; justify-content: center;
            font-size: 22px;
            box-shadow: 0 4px 12px rgba(27,94,32,0.3);
        }
        h1 {
            font-family: 'Space Grotesk', sans-serif;
            font-size: 22px; font-weight: 700;
            color: var(--color-primary-dark);
            letter-spacing: -0.02em;
            line-height: 1.2;
        }
        .subtitle {
            color: var(--color-muted);
            font-size: 12px;
            font-weight: 500;
            letter-spacing: 0.02em;
        }
        h2 {
            font-family: 'Space Grotesk', sans-serif;
            font-size: 26px; font-weight: 700;
            color: var(--color-text);
            margin-bottom: 6px;
            letter-spacing: -0.025em;
        }
        .lead {
            color: var(--color-muted);
            font-size: 13px;
            margin-bottom: 28px;
        }
        .field { margin-bottom: 16px; }
        label {
            display: block;
            font-size: 10px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--color-muted);
            margin-bottom: 6px;
        }
        .input-wrap { position: relative; }
        .input-wrap i {
            position: absolute;
            left: 14px; top: 50%; transform: translateY(-50%);
            color: var(--color-muted);
            font-size: 16px;
            pointer-events: none;
            transition: color 200ms ease;
        }
        input[type="text"], input[type="password"] {
            width: 100%;
            padding: 12px 14px 12px 42px;
            border: 1px solid var(--color-border);
            border-radius: 10px;
            font-family: inherit;
            font-size: 14px;
            background: #FAFBFA;
            transition: border-color 200ms, box-shadow 200ms, background 200ms;
        }
        input:focus {
            outline: none;
            border-color: var(--color-primary);
            background: white;
            box-shadow: 0 0 0 3px rgba(27,94,32,0.10);
        }
        input:focus + i, .input-wrap:focus-within i {
            color: var(--color-primary);
        }
        button {
            width: 100%;
            padding: 13px;
            margin-top: 8px;
            background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-family: inherit;
            font-size: 14px;
            font-weight: 600;
            letter-spacing: 0.02em;
            cursor: pointer;
            transition: transform 150ms, box-shadow 200ms, filter 200ms;
            box-shadow: 0 4px 12px rgba(27,94,32,0.25);
        }
        button:hover {
            transform: translateY(-1px);
            box-shadow: 0 8px 20px rgba(27,94,32,0.35);
            filter: brightness(1.05);
        }
        button:active { transform: translateY(0); }
        .error {
            background: rgba(198,40,40,0.08);
            border-left: 3px solid var(--color-danger);
            color: var(--color-danger);
            padding: 10px 14px;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 500;
            margin-bottom: 16px;
            display: flex; gap: 8px; align-items: center;
            animation: shake 400ms ease-out;
        }
        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            25% { transform: translateX(-4px); }
            75% { transform: translateX(4px); }
        }
        .footer {
            margin-top: 24px;
            padding-top: 20px;
            border-top: 1px solid var(--color-border);
            text-align: center;
            font-size: 11px;
            color: var(--color-muted);
        }
        .footer strong { color: var(--color-primary); font-weight: 600; }
    </style>
</head>
<body>
    <div class="login-card">
        <div class="brand">
            <div class="brand-icon"><i class="bi bi-pie-chart-fill"></i></div>
            <div>
                <h1>Dashboard Sananduva</h1>
                <div class="subtitle">RENDIMENTO DE CARCAÇAS SUÍNAS</div>
            </div>
        </div>

        <h2>Bem-vindo de volta</h2>
        <p class="lead">Acesse sua conta para visualizar os indicadores.</p>

        {% if error %}
        <div class="error">
            <i class="bi bi-exclamation-circle-fill"></i>
            <span>{{ error }}</span>
        </div>
        {% endif %}

        <form method="POST" action="/login">
            <div class="field">
                <label for="username">Usuário</label>
                <div class="input-wrap">
                    <input type="text" id="username" name="username"
                           placeholder="seu.usuario" required autofocus>
                    <i class="bi bi-person-fill"></i>
                </div>
            </div>

            <div class="field">
                <label for="password">Senha</label>
                <div class="input-wrap">
                    <input type="password" id="password" name="password"
                           placeholder="••••••••" required>
                    <i class="bi bi-lock-fill"></i>
                </div>
            </div>

            <button type="submit">
                Entrar
                <i class="bi bi-arrow-right" style="margin-left: 6px;"></i>
            </button>
        </form>

        <div class="footer">
            Sistema corporativo · <strong>Sananduva</strong>
        </div>
    </div>
</body>
</html>
"""
