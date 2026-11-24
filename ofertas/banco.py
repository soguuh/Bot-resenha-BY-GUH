"""
Banco — persistência de histórico, alertas e canais (SQLite).
O arquivo ofertas.db é criado automaticamente na raiz do projeto.
"""
from __future__ import annotations

import logging
import os
import sqlite3
from datetime import datetime
from typing import List, Optional, Tuple

from ofertas.base import Produto, AlertaPreco

logger = logging.getLogger(__name__)

# Sempre na raiz do projeto, não importa de onde o bot rodar
RAIZ_PROJETO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(RAIZ_PROJETO, "ofertas.db")


def _conectar() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def inicializar_banco():
    with _conectar() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS historico_precos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chave_produto TEXT NOT NULL,
            loja TEXT NOT NULL,
            id_produto TEXT NOT NULL,
            nome TEXT NOT NULL,
            preco REAL NOT NULL,
            url TEXT NOT NULL,
            data_registro TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_chave ON historico_precos(chave_produto);

        CREATE TABLE IF NOT EXISTS alertas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            termo_busca TEXT NOT NULL,
            preco_alvo REAL NOT NULL,
            guild_id INTEGER,
            criado_por TEXT,
            ativo INTEGER DEFAULT 1,
            criado_em TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS canais_ofertas (
            guild_id INTEGER PRIMARY KEY,
            canal_id INTEGER NOT NULL,
            configurado_em TEXT DEFAULT (datetime('now'))
        );
        """)
    logger.info("Banco pronto: %s", DB_PATH)


# ── HISTÓRICO ─────────────────────────────────────────────────

def salvar_historico(produto: Produto):
    with _conectar() as conn:
        conn.execute(
            """INSERT INTO historico_precos
               (chave_produto, loja, id_produto, nome, preco, url, data_registro)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                produto.chave_unica, produto.loja, produto.id_produto,
                produto.nome, produto.preco, produto.url,
                datetime.now().isoformat(),
            ),
        )


def obter_ultimo_preco(chave_produto: str) -> Optional[float]:
    """Último preço registrado. Chamar DEPOIS de salvar_historico
    no mesmo ciclo: o registro mais recente é o atual, este retorna
    o anterior a ele."""
    with _conectar() as conn:
        row = conn.execute(
            """SELECT preco FROM historico_precos
               WHERE chave_produto = ?
               ORDER BY id DESC LIMIT 1 OFFSET 1""",
            (chave_produto,),
        ).fetchone()
        return row["preco"] if row else None


# ── ALERTAS ───────────────────────────────────────────────────

def criar_alerta(termo: str, preco_alvo: float,
                 guild_id: int = None, criado_por: str = None) -> AlertaPreco:
    with _conectar() as conn:
        cursor = conn.execute(
            """INSERT INTO alertas (termo_busca, preco_alvo, guild_id, criado_por)
               VALUES (?, ?, ?, ?)""",
            (termo, preco_alvo, guild_id, criado_por),
        )
        return AlertaPreco(
            termo_busca=termo,
            preco_alvo=preco_alvo,
            id_alerta=str(cursor.lastrowid),
            guild_id=guild_id,
        )


def listar_alertas() -> List[AlertaPreco]:
    with _conectar() as conn:
        rows = conn.execute(
            "SELECT * FROM alertas WHERE ativo = 1"
        ).fetchall()
        return [
            AlertaPreco(
                termo_busca=r["termo_busca"],
                preco_alvo=r["preco_alvo"],
                id_alerta=str(r["id"]),
                guild_id=r["guild_id"],
            )
            for r in rows
        ]


def listar_alertas_do_servidor(guild_id: int) -> List[AlertaPreco]:
    with _conectar() as conn:
        rows = conn.execute(
            "SELECT * FROM alertas WHERE ativo = 1 AND guild_id = ?",
            (guild_id,),
        ).fetchall()
        return [
            AlertaPreco(
                termo_busca=r["termo_busca"],
                preco_alvo=r["preco_alvo"],
                id_alerta=str(r["id"]),
                guild_id=r["guild_id"],
            )
            for r in rows
        ]


def desativar_alerta(id_alerta: int) -> bool:
    with _conectar() as conn:
        cursor = conn.execute(
            "UPDATE alertas SET ativo = 0 WHERE id = ?", (id_alerta,)
        )
        return cursor.rowcount > 0


# ── CANAIS POR SERVIDOR ───────────────────────────────────────

def salvar_canal_ofertas(guild_id: int, canal_id: int):
    with _conectar() as conn:
        conn.execute(
            """INSERT INTO canais_ofertas (guild_id, canal_id)
               VALUES (?, ?)
               ON CONFLICT(guild_id) DO UPDATE SET canal_id = excluded.canal_id""",
            (guild_id, canal_id),
        )


def listar_canais_ofertas() -> List[Tuple[int, int]]:
    """[(guild_id, canal_id), ...] de todos os servidores configurados."""
    with _conectar() as conn:
        rows = conn.execute(
            "SELECT guild_id, canal_id FROM canais_ofertas"
        ).fetchall()
        return [(r["guild_id"], r["canal_id"]) for r in rows]


def obter_canal_ofertas(guild_id: int) -> Optional[int]:
    with _conectar() as conn:
        row = conn.execute(
            "SELECT canal_id FROM canais_ofertas WHERE guild_id = ?",
            (guild_id,),
        ).fetchone()
        return row["canal_id"] if row else None


def remover_canal_ofertas(guild_id: int):
    with _conectar() as conn:
        conn.execute("DELETE FROM canais_ofertas WHERE guild_id = ?", (guild_id,))


# Cria o banco assim que o módulo for importado
inicializar_banco()
