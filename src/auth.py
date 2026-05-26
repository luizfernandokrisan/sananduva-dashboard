"""Camada de autenticação. Usa SQLite e hash PBKDF2 do Werkzeug
   (sem dependências C — funciona em qualquer ambiente).
   Plug futuro: trocar `_conexao()` por Oracle quando migrar."""
import sqlite3
from pathlib import Path
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from config import SQLITE_PATH


class User(UserMixin):
    """Representação leve do usuário pro Flask-Login."""
    def __init__(self, id_: int, username: str, nome: str, role: str):
        self.id = id_
        self.username = username
        self.nome = nome
        self.role = role


def _conexao():
    return sqlite3.connect(SQLITE_PATH)


def garantir_tabela():
    """Cria tabela 'usuarios' se não existir."""
    with _conexao() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                username    TEXT    NOT NULL UNIQUE,
                nome        TEXT    NOT NULL,
                senha_hash  TEXT    NOT NULL,
                role        TEXT    NOT NULL DEFAULT 'usuario',
                criado_em   TEXT    DEFAULT CURRENT_TIMESTAMP
            )
        """)


def criar_usuario(username: str, nome: str, senha: str, role: str = "usuario"):
    garantir_tabela()
    senha_hash = generate_password_hash(senha, method="pbkdf2:sha256", salt_length=16)
    with _conexao() as con:
        try:
            con.execute(
                "INSERT INTO usuarios (username, nome, senha_hash, role) VALUES (?, ?, ?, ?)",
                (username, nome, senha_hash, role),
            )
            return True
        except sqlite3.IntegrityError:
            return False  # username já existe


def buscar_por_id(user_id: int) -> User | None:
    with _conexao() as con:
        row = con.execute(
            "SELECT id, username, nome, role FROM usuarios WHERE id = ?",
            (user_id,),
        ).fetchone()
    return User(*row) if row else None


def autenticar(username: str, senha: str) -> User | None:
    """Retorna User se credenciais válidas, senão None."""
    with _conexao() as con:
        row = con.execute(
            "SELECT id, username, nome, role, senha_hash FROM usuarios WHERE username = ?",
            (username,),
        ).fetchone()
    if row and check_password_hash(row[4], senha):
        return User(row[0], row[1], row[2], row[3])
    return None


def listar_usuarios() -> list[dict]:
    garantir_tabela()
    with _conexao() as con:
        rows = con.execute(
            "SELECT id, username, nome, role, criado_em FROM usuarios ORDER BY id"
        ).fetchall()
    return [{"id": r[0], "username": r[1], "nome": r[2],
             "role": r[3], "criado_em": r[4]} for r in rows]
