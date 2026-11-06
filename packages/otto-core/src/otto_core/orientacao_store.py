"""Perguntas progressivas de orientação (§9.1) — locais, sem perfil obrigatório."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

RESPOSTAS_VALIDAS = frozenset(
    {"sim", "nao", "nao_sei", "preciso_verificar", "nao_respondida"}
)

PERGUNTAS: list[dict[str, str]] = [
    {
        "id": "itens_pretendidos",
        "texto": "Já sabe quais itens ou lotes pretende atender?",
    },
    {
        "id": "local_prazo",
        "texto": "Consegue atender ao local e ao prazo identificados (quando houver)?",
    },
    {
        "id": "cadastros_plataforma",
        "texto": "Já verificou cadastros/plataforma mencionados nos documentos?",
    },
    {
        "id": "docs_exigidos",
        "texto": "Já listou os documentos exigidos que ainda faltam reunir?",
    },
    {
        "id": "capacidade",
        "texto": "Tem condições de demonstrar a capacidade exigida (quando descrita)?",
    },
]


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def list_orientacao(conn: sqlite3.Connection, numero: str) -> dict:
    rows = {
        r["pergunta_id"]: r
        for r in conn.execute(
            "SELECT * FROM orientacao_respostas WHERE numero_controle_pncp = ?",
            (numero,),
        ).fetchall()
    }
    items = []
    for p in PERGUNTAS:
        r = rows.get(p["id"])
        items.append(
            {
                "id": p["id"],
                "texto": p["texto"],
                "resposta": (r["resposta"] if r else "nao_respondida"),
                "detalhe": (r["detalhe"] if r else ""),
                "atualizado_em": (r["atualizado_em"] if r else None),
            }
        )
    return {
        "items": items,
        "aviso": (
            "Perguntas locais para organizar a análise. Não cadastram empresa, "
            "não comprovam elegibilidade e não enviam proposta."
        ),
    }


def upsert_orientacao(
    conn: sqlite3.Connection,
    numero: str,
    pergunta_id: str,
    resposta: str,
    detalhe: str = "",
) -> dict:
    ids = {p["id"] for p in PERGUNTAS}
    if pergunta_id not in ids:
        raise ValueError("Pergunta desconhecida.")
    resp = (resposta or "nao_respondida").strip().lower()
    if resp not in RESPOSTAS_VALIDAS:
        raise ValueError("Resposta inválida.")
    opp = conn.execute(
        "SELECT 1 FROM oportunidades WHERE numero_controle_pncp = ?", (numero,)
    ).fetchone()
    if not opp:
        raise ValueError("Oportunidade não encontrada.")
    agora = _now()
    conn.execute(
        """
        INSERT INTO orientacao_respostas (
          numero_controle_pncp, pergunta_id, resposta, detalhe, atualizado_em
        ) VALUES (?,?,?,?,?)
        ON CONFLICT(numero_controle_pncp, pergunta_id) DO UPDATE SET
          resposta=excluded.resposta,
          detalhe=excluded.detalhe,
          atualizado_em=excluded.atualizado_em
        """,
        (numero, pergunta_id, resp, detalhe or "", agora),
    )
    conn.commit()
    try:
        from otto_core.requisito_store import sincronizar_orientacao_requisito

        sincronizar_orientacao_requisito(conn, numero, pergunta_id, resp)
    except (ValueError, sqlite3.OperationalError):
        pass
    out = list_orientacao(conn, numero)
    out["aviso"] = (
        out["aviso"]
        + " Respostas “Não” / “Preciso verificar” geram requisito pendente em §9.2."
    )
    return out
