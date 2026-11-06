"""Itens e lotes estruturados (README §4/§7) — sem presumir disputa separada."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Any

AVISO = (
    "Itens de um lote não são presumidos como disputáveis separadamente. "
    "Só marque disputa separada se os documentos confirmarem. "
    "Classificação de setor/categoria do item é manual; sugestão determinística "
    "aparece identificada e não sobrescreve a escolha do usuário."
)

ORIGEM_AUTO_APLICADA = "sugestao_deterministica_aplicada"
ORIGEM_USUARIO = "usuario"


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _cols(conn: sqlite3.Connection, table: str) -> set[str]:
    return {r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}


def _sugerir(descricao: str) -> tuple[str, str]:
    from otto_core.niche import classify_nicho

    setor, _conf, _hits = classify_nicho(descricao or "")
    return setor or "", setor or ""


def _lote_row(r: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": int(r["id"]),
        "numero_controle_pncp": r["numero_controle_pncp"],
        "codigo": r["codigo"] or "",
        "descricao": r["descricao"] or "",
        "valor_estimado": r["valor_estimado"],
        "observacao": r["observacao"] or "",
        "disputa_separada_confirmada": bool(r["disputa_separada_confirmada"]),
        "atualizado_em": r["atualizado_em"],
    }


def _item_row(r: sqlite3.Row) -> dict[str, Any]:
    keys = set(r.keys())
    setor = (r["setor"] if "setor" in keys else "") or ""
    categoria = (r["categoria"] if "categoria" in keys else "") or ""
    sug_setor = (r["setor_sugerido"] if "setor_sugerido" in keys else "") or ""
    sug_cat = (r["categoria_sugerida"] if "categoria_sugerida" in keys else "") or ""
    origem = (r["classificacao_origem"] if "classificacao_origem" in keys else "") or ""
    # Sugestão em tempo real se ainda não persistida (compatível com bases antigas).
    if not sug_setor:
        sug_setor, sug_cat = _sugerir(r["descricao"] or "")
    return {
        "id": int(r["id"]),
        "numero_controle_pncp": r["numero_controle_pncp"],
        "lote_id": r["lote_id"],
        "codigo": r["codigo"] or "",
        "descricao": r["descricao"],
        "quantidade": r["quantidade"],
        "unidade": r["unidade"] or "",
        "valor_unitario": r["valor_unitario"],
        "valor_total": r["valor_total"],
        "observacao": r["observacao"] or "",
        "setor": setor,
        "categoria": categoria,
        "setor_sugerido": sug_setor,
        "categoria_sugerida": sug_cat,
        "classificacao_origem": origem,
        "atualizado_em": r["atualizado_em"],
    }


def _ensure_opp(conn: sqlite3.Connection, numero: str) -> None:
    if not conn.execute(
        "SELECT 1 FROM oportunidades WHERE numero_controle_pncp = ?", (numero,)
    ).fetchone():
        raise ValueError("Oportunidade não encontrada.")


def marcar_autoaplicacoes_existentes(conn: sqlite3.Connection) -> int:
    """Sinaliza itens que já tinham setor/categoria preenchidos sem origem de usuário.

    Não apaga nem limpa valores — só marca a origem para transparência.
    """
    cols = _cols(conn, "oportunidade_itens")
    if "classificacao_origem" not in cols or "setor" not in cols:
        return 0
    cur = conn.execute(
        """
        UPDATE oportunidade_itens
        SET classificacao_origem = ?
        WHERE (IFNULL(setor,'') != '' OR IFNULL(categoria,'') != '')
          AND IFNULL(classificacao_origem,'') = ''
        """,
        (ORIGEM_AUTO_APLICADA,),
    )
    conn.commit()
    return int(cur.rowcount or 0)


def list_itens_lotes(conn: sqlite3.Connection, numero: str) -> dict[str, Any]:
    _ensure_opp(conn, numero)
    lotes = [
        _lote_row(r)
        for r in conn.execute(
            "SELECT * FROM oportunidade_lotes WHERE numero_controle_pncp = ? ORDER BY id",
            (numero,),
        )
    ]
    itens = [
        _item_row(r)
        for r in conn.execute(
            "SELECT * FROM oportunidade_itens WHERE numero_controle_pncp = ? ORDER BY id",
            (numero,),
        )
    ]
    n_auto = sum(1 for i in itens if i["classificacao_origem"] == ORIGEM_AUTO_APLICADA)
    aviso = AVISO
    if n_auto:
        aviso += (
            f" {n_auto} item(ns) nesta oportunidade têm classificação marcada como "
            f"“{ORIGEM_AUTO_APLICADA}” (aplicada antes da correção; valores preservados)."
        )
    return {"lotes": lotes, "itens": itens, "aviso": aviso}


def add_lote(
    conn: sqlite3.Connection,
    numero: str,
    *,
    codigo: str = "",
    descricao: str = "",
    valor_estimado: float | None = None,
    observacao: str = "",
    disputa_separada_confirmada: bool = False,
) -> dict[str, Any]:
    _ensure_opp(conn, numero)
    cur = conn.execute(
        """
        INSERT INTO oportunidade_lotes (
          numero_controle_pncp, codigo, descricao, valor_estimado, observacao,
          disputa_separada_confirmada, atualizado_em
        ) VALUES (?,?,?,?,?,?,?)
        """,
        (
            numero,
            codigo or "",
            descricao or "",
            valor_estimado,
            observacao or "",
            1 if disputa_separada_confirmada else 0,
            _now(),
        ),
    )
    conn.commit()
    r = conn.execute(
        "SELECT * FROM oportunidade_lotes WHERE id = ?", (cur.lastrowid,)
    ).fetchone()
    return _lote_row(r)


def add_item(
    conn: sqlite3.Connection,
    numero: str,
    *,
    descricao: str,
    lote_id: int | None = None,
    codigo: str = "",
    quantidade: float | None = None,
    unidade: str = "",
    valor_unitario: float | None = None,
    valor_total: float | None = None,
    observacao: str = "",
    setor: str = "",
    categoria: str = "",
) -> dict[str, Any]:
    """Cria item. Setor/categoria só entram se o usuário informar; sugestão não sobrescreve."""
    _ensure_opp(conn, numero)
    desc = (descricao or "").strip()
    if not desc:
        raise ValueError("Descrição do item é obrigatória.")
    if lote_id is not None:
        lote = conn.execute(
            """
            SELECT 1 FROM oportunidade_lotes
            WHERE id = ? AND numero_controle_pncp = ?
            """,
            (lote_id, numero),
        ).fetchone()
        if not lote:
            raise ValueError("Lote não encontrado nesta oportunidade.")
    sug_setor, sug_cat = _sugerir(desc)
    setor_u = (setor or "").strip()
    cat_u = (categoria or "").strip()
    origem = ORIGEM_USUARIO if (setor_u or cat_u) else ""
    cols = _cols(conn, "oportunidade_itens")
    if "setor_sugerido" in cols and "classificacao_origem" in cols:
        cur = conn.execute(
            """
            INSERT INTO oportunidade_itens (
              numero_controle_pncp, lote_id, codigo, descricao, quantidade, unidade,
              valor_unitario, valor_total, observacao, setor, categoria,
              setor_sugerido, categoria_sugerida, classificacao_origem, atualizado_em
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                numero,
                lote_id,
                codigo or "",
                desc,
                quantidade,
                unidade or "",
                valor_unitario,
                valor_total,
                observacao or "",
                setor_u,
                cat_u,
                sug_setor,
                sug_cat,
                origem,
                _now(),
            ),
        )
    elif "setor" in cols:
        # Compatibilidade: não aplicar sugestão automaticamente.
        cur = conn.execute(
            """
            INSERT INTO oportunidade_itens (
              numero_controle_pncp, lote_id, codigo, descricao, quantidade, unidade,
              valor_unitario, valor_total, observacao, setor, categoria, atualizado_em
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                numero,
                lote_id,
                codigo or "",
                desc,
                quantidade,
                unidade or "",
                valor_unitario,
                valor_total,
                observacao or "",
                setor_u,
                cat_u,
                _now(),
            ),
        )
    else:
        cur = conn.execute(
            """
            INSERT INTO oportunidade_itens (
              numero_controle_pncp, lote_id, codigo, descricao, quantidade, unidade,
              valor_unitario, valor_total, observacao, atualizado_em
            ) VALUES (?,?,?,?,?,?,?,?,?,?)
            """,
            (
                numero,
                lote_id,
                codigo or "",
                desc,
                quantidade,
                unidade or "",
                valor_unitario,
                valor_total,
                observacao or "",
                _now(),
            ),
        )
    conn.commit()
    r = conn.execute(
        "SELECT * FROM oportunidade_itens WHERE id = ?", (cur.lastrowid,)
    ).fetchone()
    return _item_row(r)


def update_item(
    conn: sqlite3.Connection,
    numero: str,
    item_id: int,
    *,
    setor: str | None = None,
    categoria: str | None = None,
    descricao: str | None = None,
    observacao: str | None = None,
) -> dict[str, Any]:
    """Edição manual de classificação (e campos básicos). Preserva valores não enviados."""
    row = conn.execute(
        "SELECT * FROM oportunidade_itens WHERE id = ? AND numero_controle_pncp = ?",
        (item_id, numero),
    ).fetchone()
    if not row:
        raise ValueError("Item não encontrado.")
    keys = set(row.keys())
    novo_setor = (setor if setor is not None else (row["setor"] if "setor" in keys else "")) or ""
    nova_cat = (
        categoria if categoria is not None else (row["categoria"] if "categoria" in keys else "")
    ) or ""
    nova_desc = descricao if descricao is not None else row["descricao"]
    nova_obs = observacao if observacao is not None else (row["observacao"] or "")
    origem = row["classificacao_origem"] if "classificacao_origem" in keys else ""
    if setor is not None or categoria is not None:
        origem = ORIGEM_USUARIO if (novo_setor or nova_cat) else ""
    sug_setor, sug_cat = _sugerir(nova_desc or "")
    cols = _cols(conn, "oportunidade_itens")
    if "classificacao_origem" in cols:
        conn.execute(
            """
            UPDATE oportunidade_itens SET
              descricao=?, observacao=?, setor=?, categoria=?,
              setor_sugerido=?, categoria_sugerida=?, classificacao_origem=?, atualizado_em=?
            WHERE id=?
            """,
            (
                nova_desc,
                nova_obs,
                novo_setor,
                nova_cat,
                sug_setor,
                sug_cat,
                origem,
                _now(),
                item_id,
            ),
        )
    elif "setor" in cols:
        conn.execute(
            """
            UPDATE oportunidade_itens SET
              descricao=?, observacao=?, setor=?, categoria=?, atualizado_em=?
            WHERE id=?
            """,
            (nova_desc, nova_obs, novo_setor, nova_cat, _now(), item_id),
        )
    else:
        conn.execute(
            """
            UPDATE oportunidade_itens SET descricao=?, observacao=?, atualizado_em=?
            WHERE id=?
            """,
            (nova_desc, nova_obs, _now(), item_id),
        )
    conn.commit()
    return _item_row(
        conn.execute("SELECT * FROM oportunidade_itens WHERE id = ?", (item_id,)).fetchone()
    )


def update_lote(
    conn: sqlite3.Connection,
    numero: str,
    lote_id: int,
    *,
    disputa_separada_confirmada: bool | None = None,
    descricao: str | None = None,
    codigo: str | None = None,
    valor_estimado: float | None = None,
    observacao: str | None = None,
) -> dict[str, Any]:
    row = conn.execute(
        "SELECT * FROM oportunidade_lotes WHERE id = ? AND numero_controle_pncp = ?",
        (lote_id, numero),
    ).fetchone()
    if not row:
        raise ValueError("Lote não encontrado.")
    disp = (
        int(bool(disputa_separada_confirmada))
        if disputa_separada_confirmada is not None
        else row["disputa_separada_confirmada"]
    )
    conn.execute(
        """
        UPDATE oportunidade_lotes SET
          codigo=?, descricao=?, valor_estimado=?, observacao=?,
          disputa_separada_confirmada=?, atualizado_em=?
        WHERE id=?
        """,
        (
            codigo if codigo is not None else row["codigo"],
            descricao if descricao is not None else row["descricao"],
            valor_estimado if valor_estimado is not None else row["valor_estimado"],
            observacao if observacao is not None else row["observacao"],
            disp,
            _now(),
            lote_id,
        ),
    )
    conn.commit()
    return _lote_row(
        conn.execute("SELECT * FROM oportunidade_lotes WHERE id = ?", (lote_id,)).fetchone()
    )
