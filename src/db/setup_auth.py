"""Cria a tabela de usuários e popula com 3 contas demo.
   Roda UMA vez antes do primeiro login:
       python src/db/setup_auth.py
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from auth import garantir_tabela, criar_usuario, listar_usuarios


USUARIOS_DEMO = [
    # (username, nome_completo, senha, role)
    ("admin",   "Administrador",        "admin@2026",   "admin"),
    ("diretor", "Diretor Industrial",   "diretor@2026", "diretor"),
    ("luiz",    "Luiz Fernando Krisan", "luiz@2026",    "analista"),
]


def main():
    garantir_tabela()
    print("Tabela 'usuarios' OK.\n")

    for username, nome, senha, role in USUARIOS_DEMO:
        ok = criar_usuario(username, nome, senha, role)
        status = "✓ criado" if ok else "↩ já existia"
        print(f"  {status:14s} {username:10s} ({role}) — senha: {senha}")

    print("\nUsuários atuais:")
    for u in listar_usuarios():
        print(f"  #{u['id']:<3d} {u['username']:10s} {u['nome']:30s} role={u['role']}")

    print("\n⚠  TROQUE AS SENHAS antes de colocar em rede corporativa.")


if __name__ == "__main__":
    main()
