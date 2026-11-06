"""Log local de ações do usuário (README §19) — sem login/multiusuário."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def registrar(
    conn: sqlite3.Connection,
    acao: str,
    *,
    numero: str | None = None,
    detalhe: str = "",
) -> None:
    conn.execute(
        """
        INSERT INTO auditoria_acoes (acao, numero_controle_pncp, detalhe, criado_em)
        VALUES (?,?,?,?)
        """,
        ((acao or "").strip() or "acao", numero, (detalhe or "")[:500], _now()),
    )
    conn.commit()


def listar(conn: sqlite3.Connection, *, limit: int = 100) -> dict[str, Any]:
    rows = conn.execute(
        """
        SELECT id, acao, numero_controle_pncp, detalhe, criado_em
        FROM auditoria_acoes
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return {
        "items": [
            {
                "id": int(r["id"]),
                "acao": r["acao"],
                "numero_controle_pncp": r["numero_controle_pncp"],
                "detalhe": r["detalhe"] or "",
                "criado_em": r["criado_em"],
            }
            for r in rows
        ],
        "aviso": "Registro local neste computador. Não identifica usuário de rede nem substitui backup.",
    }
