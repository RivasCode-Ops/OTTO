"""Verificação por requisito (README §9.2) — local; sem declarar habilitação."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Any

from otto_core.document_store import mime_exige_pagina

ESTADOS = frozenset(
    {
        "evidencia_cadastrada",
        "declaracao_usuario",
        "pendente_confirmacao",
        "nao_atendido",
        "nao_avaliado",
    }
)

AVISO = (
    "Documento cadastrado não significa documento validado. "
    "Este registro não declara habilitação definitiva nem envia proposta. "
    "Evidência aponta para a versão específica do documento (id); página é opcional "
    "(ex.: TXT). Nova versão do arquivo sinaliza revisão sem apagar o vínculo antigo."
)

ORIENTACAO_PARA_REQUISITO: dict[str, str] = {
    "itens_pretendidos": "Definir itens/lotes pretendidos (orientação)",
    "local_prazo": "Confirmar local e prazo de atendimento (orientação)",
    "cadastros_plataforma": "Verificar cadastros/plataforma mencionados (orientação)",
    "docs_exigidos": "Reunir documentos exigidos ainda faltantes (orientação)",
    "capacidade": "Demonstrar capacidade exigida (orientação)",
}

REVISAO_USUARIO = "usuario"


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _cols(r: sqlite3.Row) -> set[str]:
    return set(r.keys())


def _doc_meta(conn: sqlite3.Connection, doc_id: int | None) -> dict[str, Any] | None:
    if not doc_id:
        return None
    d = conn.execute(
        "SELECT id, nome_original, versao, tipo_mime, documento_anterior_id FROM oportunidade_documentos WHERE id = ?",
        (doc_id,),
    ).fetchone()
    if not d:
        return None
    return {
        "id": int(d["id"]),
        "nome_original": d["nome_original"],
        "versao": int(d["versao"]),
        "tipo_mime": d["tipo_mime"] or "",
        "documento_anterior_id": d["documento_anterior_id"],
        "pagina_aplicavel": mime_exige_pagina(d["tipo_mime"]),
    }


def _row(conn: sqlite3.Connection, r: sqlite3.Row) -> dict[str, Any]:
    keys = _cols(r)
    doc_id = r["evidencia_documento_id"]
    pagina = r["evidencia_pagina"] if "evidencia_pagina" in keys else None
    return {
        "id": int(r["id"]),
        "numero_controle_pncp": r["numero_controle_pncp"],
        "descricao": r["descricao"],
        "origem": r["origem"] or "usuario",
        "estado": r["estado"],
        "evidencia_documento_id": doc_id,
        "evidencia_pagina": pagina,
        "evidencia_trecho": r["evidencia_trecho"] or "",
        "precisa_revisao": bool(r["precisa_revisao"]) if "precisa_revisao" in keys else False,
        "revisao_origem": (r["revisao_origem"] if "revisao_origem" in keys else "") or "",
        "observacao": r["observacao"] or "",
        "atualizado_em": r["atualizado_em"],
        "evidencia_documento": _doc_meta(conn, int(doc_id) if doc_id else None),
    }


def list_requisitos(conn: sqlite3.Connection, numero: str) -> dict[str, Any]:
    rows = conn.execute(
        """
        SELECT * FROM requisitos_verificacao
        WHERE numero_controle_pncp = ?
        ORDER BY id
        """,
        (numero,),
    ).fetchall()
    return {"items": [_row(conn, r) for r in rows], "aviso": AVISO}


def add_requisito(
    conn: sqlite3.Connection,
    numero: str,
    descricao: str,
    *,
    origem: str = "usuario",
    estado: str = "nao_avaliado",
) -> dict[str, Any]:
    opp = conn.execute(
        "SELECT 1 FROM oportunidades WHERE numero_controle_pncp = ?", (numero,)
    ).fetchone()
    if not opp:
        raise ValueError("Oportunidade não encontrada.")
    desc = (descricao or "").strip()
    if not desc:
        raise ValueError("Descrição do requisito é obrigatória.")
    est = (estado or "nao_avaliado").strip()
    if est not in ESTADOS:
        raise ValueError("Estado de verificação inválido.")
    agora = _now()
    cols = {r[1] for r in conn.execute("PRAGMA table_info(requisitos_verificacao)").fetchall()}
    if "evidencia_pagina" in cols:
        cur = conn.execute(
            """
            INSERT INTO requisitos_verificacao (
              numero_controle_pncp, descricao, origem, estado,
              evidencia_documento_id, evidencia_pagina, evidencia_trecho,
              precisa_revisao, revisao_origem, observacao, atualizado_em
            ) VALUES (?,?,?,?,NULL,NULL,'',0,'','',?)
            """,
            (numero, desc, origem or "usuario", est, agora),
        )
    else:
        cur = conn.execute(
            """
            INSERT INTO requisitos_verificacao (
              numero_controle_pncp, descricao, origem, estado,
              evidencia_documento_id, evidencia_trecho, observacao, atualizado_em
            ) VALUES (?,?,?,?,NULL,'','',?)
            """,
            (numero, desc, origem or "usuario", est, agora),
        )
    conn.commit()
    r = conn.execute(
        "SELECT * FROM requisitos_verificacao WHERE id = ?", (cur.lastrowid,)
    ).fetchone()
    return _row(conn, r)


def update_requisito(
    conn: sqlite3.Connection,
    numero: str,
    req_id: int,
    *,
    estado: str | None = None,
    evidencia_documento_id: int | None = None,
    limpar_evidencia_doc: bool = False,
    evidencia_pagina: int | None = None,
    limpar_evidencia_pagina: bool = False,
    evidencia_trecho: str | None = None,
    observacao: str | None = None,
    descricao: str | None = None,
    confirmar_revisao_usuario: bool = False,
) -> dict[str, Any]:
    row = conn.execute(
        """
        SELECT * FROM requisitos_verificacao
        WHERE id = ? AND numero_controle_pncp = ?
        """,
        (req_id, numero),
    ).fetchone()
    if not row:
        raise ValueError("Requisito não encontrado.")
    keys = _cols(row)
    est = estado if estado is not None else row["estado"]
    if est not in ESTADOS:
        raise ValueError("Estado de verificação inválido.")
    if limpar_evidencia_doc:
        ev_doc = None
    elif evidencia_documento_id is not None:
        ev_doc = evidencia_documento_id
        # Valida que o documento pertence à oportunidade
        d = conn.execute(
            """
            SELECT 1 FROM oportunidade_documentos
            WHERE id = ? AND numero_controle_pncp = ?
            """,
            (ev_doc, numero),
        ).fetchone()
        if not d:
            raise ValueError("Documento de evidência não encontrado nesta oportunidade.")
    else:
        ev_doc = row["evidencia_documento_id"]

    if limpar_evidencia_pagina:
        ev_pag = None
    elif evidencia_pagina is not None:
        ev_pag = evidencia_pagina
    else:
        ev_pag = row["evidencia_pagina"] if "evidencia_pagina" in keys else None

    # Não inventar página: TXT/DOCX sem paginação física → página NULL.
    if ev_doc and ev_pag is not None:
        mime = conn.execute(
            "SELECT tipo_mime FROM oportunidade_documentos WHERE id = ?", (ev_doc,)
        ).fetchone()
        if mime and not mime_exige_pagina(str(mime["tipo_mime"] or "")):
            ev_pag = None

    ev_trecho = (
        evidencia_trecho if evidencia_trecho is not None else (row["evidencia_trecho"] or "")
    )
    obs = observacao if observacao is not None else (row["observacao"] or "")
    desc = descricao if descricao is not None else row["descricao"]
    precisa = int(row["precisa_revisao"]) if "precisa_revisao" in keys else 0
    rev_orig = (row["revisao_origem"] if "revisao_origem" in keys else "") or ""
    if confirmar_revisao_usuario or (
        evidencia_documento_id is not None or evidencia_trecho is not None or evidencia_pagina is not None
    ):
        # Alterar evidência ou confirmar = revisão pelo usuário (nunca automática).
        precisa = 0
        rev_orig = REVISAO_USUARIO

    cols = {r[1] for r in conn.execute("PRAGMA table_info(requisitos_verificacao)").fetchall()}
    if "evidencia_pagina" in cols and "precisa_revisao" in cols:
        conn.execute(
            """
            UPDATE requisitos_verificacao SET
              descricao=?, estado=?, evidencia_documento_id=?, evidencia_pagina=?,
              evidencia_trecho=?, precisa_revisao=?, revisao_origem=?, observacao=?, atualizado_em=?
            WHERE id=?
            """,
            (desc, est, ev_doc, ev_pag, ev_trecho, precisa, rev_orig, obs, _now(), req_id),
        )
    else:
        conn.execute(
            """
            UPDATE requisitos_verificacao SET
              descricao=?, estado=?, evidencia_documento_id=?, evidencia_trecho=?,
              observacao=?, atualizado_em=?
            WHERE id=?
            """,
            (desc, est, ev_doc, ev_trecho, obs, _now(), req_id),
        )
    conn.commit()
    r = conn.execute(
        "SELECT * FROM requisitos_verificacao WHERE id = ?", (req_id,)
    ).fetchone()
    return _row(conn, r)


def marcar_requisitos_para_revisao(
    conn: sqlite3.Connection,
    numero: str,
    *,
    documento_ids_antigos: list[int],
    motivo: str,
) -> int:
    """Sinaliza requisitos cuja evidência aponta para versões anteriores — não altera o vínculo."""
    cols = {r[1] for r in conn.execute("PRAGMA table_info(requisitos_verificacao)").fetchall()}
    if "precisa_revisao" not in cols or not documento_ids_antigos:
        return 0
    ph = ",".join("?" * len(documento_ids_antigos))
    cur = conn.execute(
        f"""
        UPDATE requisitos_verificacao
        SET precisa_revisao = 1, revisao_origem = '',
            observacao = CASE
              WHEN TRIM(observacao) = '' THEN ?
              ELSE observacao || ' | ' || ?
            END,
            atualizado_em = ?
        WHERE numero_controle_pncp = ?
          AND evidencia_documento_id IN ({ph})
        """,
        [motivo[:200], motivo[:200], _now(), numero, *documento_ids_antigos],
    )
    conn.commit()
    return int(cur.rowcount or 0)


def _existe_origem(conn: sqlite3.Connection, numero: str, origem: str) -> bool:
    return (
        conn.execute(
            """
            SELECT 1 FROM requisitos_verificacao
            WHERE numero_controle_pncp = ? AND origem = ?
            LIMIT 1
            """,
            (numero, origem),
        ).fetchone()
        is not None
    )


def sincronizar_orientacao_requisito(
    conn: sqlite3.Connection,
    numero: str,
    pergunta_id: str,
    resposta: str,
) -> dict[str, Any] | None:
    desc = ORIENTACAO_PARA_REQUISITO.get(pergunta_id)
    if not desc:
        return None
    origem = f"orientacao:{pergunta_id}"
    if resposta not in {"nao", "preciso_verificar"}:
        return None
    if _existe_origem(conn, numero, origem):
        return None
    return add_requisito(
        conn,
        numero,
        desc,
        origem=origem,
        estado="pendente_confirmacao",
    )


def gerar_requisitos_da_ficha(conn: sqlite3.Connection, numero: str) -> dict[str, Any]:
    from otto_core.analise_store import ensure_ficha

    ficha = ensure_ficha(conn, numero)
    criados: list[dict[str, Any]] = []
    existentes = {
        (r["descricao"] or "").strip().lower()
        for r in list_requisitos(conn, numero)["items"]
    }
    for campo in ficha.campos:
        if campo.chave not in {"docs_requisitos", "pendencias"}:
            continue
        valor = (campo.valor or "").strip()
        if not valor:
            continue
        for linha in valor.replace(";", "\n").splitlines():
            texto = linha.strip(" -\t•*")
            if len(texto) < 3:
                continue
            key = texto.lower()
            if key in existentes:
                continue
            origem = f"ficha:{campo.chave}"
            item = add_requisito(
                conn,
                numero,
                texto[:500],
                origem=origem,
                estado="nao_avaliado",
            )
            criados.append(item)
            existentes.add(key)
    pack = list_requisitos(conn, numero)
    pack["gerados"] = len(criados)
    pack["aviso"] = (
        AVISO
        + f" Gerados {len(criados)} requisito(s) a partir da ficha (campos docs_requisitos/pendencias)."
    )
    return pack


def checklist_from_requisito(conn: sqlite3.Connection, numero: str, req_id: int):
    """Gera item de checklist (tarefa) vinculado ao requisito — sem apagar evidência."""
    from otto_core.analise_store import add_checklist_item
    from otto_core.models import ChecklistItemCreate

    row = conn.execute(
        """
        SELECT * FROM requisitos_verificacao
        WHERE id = ? AND numero_controle_pncp = ?
        """,
        (req_id, numero),
    ).fetchone()
    if not row:
        raise ValueError("Requisito não encontrado.")
    keys = _cols(row)
    return add_checklist_item(
        conn,
        numero,
        ChecklistItemCreate(
            titulo=f"Providenciar: {row['descricao'][:120]}",
            descricao=(row["observacao"] or "")[:500],
            requisito_chave=f"requisito:{req_id}",
            categoria="requisito_verificacao",
            evidencia_documento_id=row["evidencia_documento_id"],
            evidencia_pagina=row["evidencia_pagina"] if "evidencia_pagina" in keys else None,
            evidencia_trecho=row["evidencia_trecho"] or "",
        ),
    )
