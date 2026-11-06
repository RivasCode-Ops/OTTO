"""Ficha de análise revisável + checklist (sem IA)."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from otto_core.models import (
    AnaliseCampo,
    AnaliseCampoUpdate,
    AnaliseFicha,
    ChecklistItem,
    ChecklistItemCreate,
    ChecklistItemUpdate,
    NaturezaCampo,
    StatusChecklist,
    StatusFicha,
)

AVISO_SEM_IA = (
    "Esta ficha combina coleta PNCP, preenchimento seu e, quando disponível, "
    "sugestões de IA local (somente neste computador — sem nuvem). "
    "Sugestões da IA não são confirmação: revise antes de aplicar. "
    "Texto de PDF por página; TXT/DOCX como bloco (página opcional). OCR local em PDF só-imagem."
)

CAMPOS_FICHA: list[tuple[str, str]] = [
    ("objeto", "Objeto"),
    ("orgao", "Órgão"),
    ("itens_lotes", "Itens e lotes"),
    ("quantidades", "Quantidades"),
    ("valores", "Valores e natureza"),
    ("datas_prazos", "Datas e prazos"),
    ("local_entrega", "Local de entrega ou execução"),
    ("docs_requisitos", "Documentos e requisitos de participação"),
    ("condicoes_execucao", "Condições de execução"),
    ("pendencias", "Pendências e pontos de atenção"),
]


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _parse_dt(v: str | None) -> datetime | None:
    if not v:
        return None
    try:
        return datetime.fromisoformat(v)
    except ValueError:
        return None


def _cols(row: sqlite3.Row) -> set[str]:
    return set(row.keys())


def _row_campo(r: sqlite3.Row) -> AnaliseCampo:
    keys = _cols(r)
    return AnaliseCampo(
        id=r["id"],
        chave=r["chave"],
        rotulo=r["rotulo"],
        valor=r["valor"] or "",
        natureza=r["natureza"],  # type: ignore[arg-type]
        documento_id=r["documento_id"],
        pagina=r["pagina"],
        trecho=r["trecho"] or "",
        precisa_revisao=bool(r["precisa_revisao"]) if "precisa_revisao" in keys else False,
        revisao_origem=(r["revisao_origem"] if "revisao_origem" in keys else "") or "",
        atualizado_em=_parse_dt(r["atualizado_em"]),
    )


def _row_checklist(r: sqlite3.Row) -> ChecklistItem:
    keys = _cols(r)
    return ChecklistItem(
        id=r["id"],
        numero_controle_pncp=r["numero_controle_pncp"],
        titulo=r["titulo"],
        descricao=r["descricao"] or "",
        status=r["status"],  # type: ignore[arg-type]
        requisito_chave=r["requisito_chave"] or "",
        categoria=(r["categoria"] if "categoria" in keys else "") or "",
        observacao=(r["observacao"] if "observacao" in keys else "") or "",
        prazo_conhecido=(r["prazo_conhecido"] if "prazo_conhecido" in keys else "") or "",
        responsavel=(r["responsavel"] if "responsavel" in keys else "") or "",
        evidencia_documento_id=r["evidencia_documento_id"],
        evidencia_pagina=r["evidencia_pagina"],
        evidencia_trecho=r["evidencia_trecho"] or "",
        atualizado_em=_parse_dt(r["atualizado_em"]),
    )


def _valores_coleta(conn: sqlite3.Connection, numero: str) -> dict[str, str]:
    r = conn.execute(
        """
        SELECT objeto_compra, orgao_razao_social, uf, municipio_ibge,
               valor_total_estimado, valor_total_homologado,
               data_publicacao, data_abertura, data_encerramento,
               modalidade, situacao, link_sistema_origem
        FROM oportunidades WHERE numero_controle_pncp = ?
        """,
        (numero,),
    ).fetchone()
    if not r:
        return {}
    vals: dict[str, str] = {}
    vals["objeto"] = (r["objeto_compra"] or "").strip()
    vals["orgao"] = (r["orgao_razao_social"] or "").strip()
    local = " · ".join(
        x for x in [(r["municipio_ibge"] or "").strip(), (r["uf"] or "").strip()] if x
    )
    vals["local_entrega"] = local
    partes_val = []
    if r["valor_total_estimado"] is not None:
        partes_val.append(f"Estimado (coleta): {r['valor_total_estimado']}")
    if r["valor_total_homologado"] is not None:
        partes_val.append(f"Homologado (coleta): {r['valor_total_homologado']}")
    vals["valores"] = "; ".join(partes_val)
    datas = []
    if r["data_publicacao"]:
        datas.append(f"Publicação: {r['data_publicacao']}")
    if r["data_abertura"]:
        datas.append(f"Abertura de propostas: {r['data_abertura']}")
    if r["data_encerramento"]:
        datas.append(f"Encerramento de propostas: {r['data_encerramento']}")
    vals["datas_prazos"] = "; ".join(datas)
    vals["itens_lotes"] = ""
    vals["quantidades"] = ""
    vals["docs_requisitos"] = ""
    vals["condicoes_execucao"] = ""
    pend = []
    if not r["link_sistema_origem"]:
        pend.append("Link original da fonte não informado na coleta.")
    pend.append(
        "Itens/lotes, quantidades, requisitos e condições de execução "
        "não foram inferidos automaticamente do edital."
    )
    vals["pendencias"] = " ".join(pend)
    return vals


def _contar_docs(conn: sqlite3.Connection, numero: str) -> int:
    r = conn.execute(
        "SELECT COUNT(*) AS c FROM oportunidade_documentos WHERE numero_controle_pncp = ?",
        (numero,),
    ).fetchone()
    return int(r["c"]) if r else 0


def marcar_ficha_desatualizada(
    conn: sqlite3.Connection,
    numero: str,
    motivo: str,
    *,
    documento_ids_antigos: list[int] | None = None,
) -> None:
    """Nova versão de documento: não apaga valores nem troca evidências; exige revisão."""
    row = conn.execute(
        "SELECT id, status FROM analise_fichas WHERE numero_controle_pncp = ?",
        (numero,),
    ).fetchone()
    if not row:
        return
    agora = _now()
    conn.execute(
        """
        UPDATE analise_fichas
        SET status = 'desatualizada', motivo_desatualizacao = ?, atualizado_em = ?, aviso = ?
        WHERE id = ?
        """,
        (motivo, agora, AVISO_SEM_IA + " " + motivo, row["id"]),
    )
    cols = {r[1] for r in conn.execute("PRAGMA table_info(analise_campos)").fetchall()}
    if "revisao_origem" in cols:
        conn.execute(
            """
            UPDATE analise_campos
            SET precisa_revisao = 1, revisao_origem = ''
            WHERE ficha_id = ?
              AND (natureza IN ('usuario', 'extraido') OR documento_id IS NOT NULL OR LENGTH(TRIM(trecho)) > 0)
            """,
            (row["id"],),
        )
    else:
        conn.execute(
            """
            UPDATE analise_campos
            SET precisa_revisao = 1
            WHERE ficha_id = ?
              AND (natureza IN ('usuario', 'extraido') OR documento_id IS NOT NULL OR LENGTH(TRIM(trecho)) > 0)
            """,
            (row["id"],),
        )
    conn.commit()
    if documento_ids_antigos:
        from otto_core.requisito_store import marcar_requisitos_para_revisao

        marcar_requisitos_para_revisao(
            conn,
            numero,
            documento_ids_antigos=documento_ids_antigos,
            motivo=motivo,
        )


def confirmar_revisao_ficha(conn: sqlite3.Connection, numero: str) -> AnaliseFicha:
    """Usuário confirma revisão — marca origem 'usuario'; nunca confirmação automática."""
    ficha = ensure_ficha(conn, numero, preservar_desatualizada=False)
    agora = _now()
    cols = {r[1] for r in conn.execute("PRAGMA table_info(analise_campos)").fetchall()}
    if "revisao_origem" in cols:
        conn.execute(
            """
            UPDATE analise_campos
            SET precisa_revisao = 0, revisao_origem = 'usuario'
            WHERE ficha_id = ?
            """,
            (ficha.id,),
        )
    else:
        conn.execute(
            "UPDATE analise_campos SET precisa_revisao = 0 WHERE ficha_id = ?",
            (ficha.id,),
        )
    conn.execute(
        """
        UPDATE analise_fichas
        SET motivo_desatualizacao = '', atualizado_em = ?
        WHERE id = ?
        """,
        (agora, ficha.id),
    )
    # Requisitos da oportunidade: confirmar revisão pelo usuário sem apagar evidência.
    rcols = {r[1] for r in conn.execute("PRAGMA table_info(requisitos_verificacao)").fetchall()}
    if "precisa_revisao" in rcols and "revisao_origem" in rcols:
        conn.execute(
            """
            UPDATE requisitos_verificacao
            SET precisa_revisao = 0, revisao_origem = 'usuario', atualizado_em = ?
            WHERE numero_controle_pncp = ? AND precisa_revisao = 1
            """,
            (agora, numero),
        )
    conn.commit()
    return ensure_ficha(conn, numero, preservar_desatualizada=False)


def _status_ficha(
    conn: sqlite3.Connection,
    numero: str,
    campos: list[AnaliseCampo],
    status_atual: str | None,
    preservar_desatualizada: bool,
) -> StatusFicha:
    if preservar_desatualizada and status_atual == "desatualizada":
        return "desatualizada"
    if any(c.precisa_revisao for c in campos):
        return "desatualizada"
    n_docs = _contar_docs(conn, numero)
    if n_docs == 0:
        return "aguardando_documentos"
    usuario = any(c.natureza == "usuario" and (c.valor or "").strip() for c in campos)
    if usuario:
        return "revisao_humana"
    return "parcial"


def ensure_ficha(
    conn: sqlite3.Connection, numero: str, *, preservar_desatualizada: bool = True
) -> AnaliseFicha:
    opp = conn.execute(
        "SELECT 1 FROM oportunidades WHERE numero_controle_pncp = ?", (numero,)
    ).fetchone()
    if not opp:
        raise ValueError("Oportunidade não encontrada.")

    row = conn.execute(
        "SELECT * FROM analise_fichas WHERE numero_controle_pncp = ?", (numero,)
    ).fetchone()
    agora = _now()
    motivo = ""
    status_atual = None
    if not row:
        cur = conn.execute(
            """
            INSERT INTO analise_fichas (numero_controle_pncp, status, atualizado_em, aviso)
            VALUES (?,?,?,?)
            """,
            (numero, "aguardando_documentos", agora, AVISO_SEM_IA),
        )
        ficha_id = int(cur.lastrowid)
    else:
        ficha_id = int(row["id"])
        status_atual = row["status"]
        keys = _cols(row)
        motivo = (row["motivo_desatualizacao"] if "motivo_desatualizacao" in keys else "") or ""

    coleta = _valores_coleta(conn, numero)
    for chave, rotulo in CAMPOS_FICHA:
        existente = conn.execute(
            "SELECT id, natureza, valor FROM analise_campos WHERE ficha_id = ? AND chave = ?",
            (ficha_id, chave),
        ).fetchone()
        valor_coleta = coleta.get(chave, "")
        if existente is None:
            conn.execute(
                """
                INSERT INTO analise_campos (
                  ficha_id, chave, rotulo, valor, natureza,
                  documento_id, pagina, trecho, atualizado_em
                ) VALUES (?,?,?,?,?,?,?,?,?)
                """,
                (
                    ficha_id,
                    chave,
                    rotulo,
                    valor_coleta,
                    "coleta" if valor_coleta else "nao_confirmado",
                    None,
                    None,
                    "",
                    agora,
                ),
            )
        elif existente["natureza"] == "coleta":
            natureza: NaturezaCampo = "coleta" if valor_coleta else "nao_confirmado"
            conn.execute(
                """
                UPDATE analise_campos
                SET valor = ?, natureza = ?, rotulo = ?, atualizado_em = ?
                WHERE id = ?
                """,
                (valor_coleta, natureza, rotulo, agora, existente["id"]),
            )

    campos = [
        _row_campo(r)
        for r in conn.execute(
            "SELECT * FROM analise_campos WHERE ficha_id = ? ORDER BY id", (ficha_id,)
        ).fetchall()
    ]
    status = _status_ficha(conn, numero, campos, status_atual, preservar_desatualizada)
    if status != "desatualizada":
        motivo = ""
    conn.execute(
        """
        UPDATE analise_fichas
        SET status = ?, atualizado_em = ?, aviso = ?, motivo_desatualizacao = ?
        WHERE id = ?
        """,
        (status, agora, AVISO_SEM_IA, motivo, ficha_id),
    )
    conn.commit()
    return AnaliseFicha(
        id=ficha_id,
        numero_controle_pncp=numero,
        status=status,
        atualizado_em=_parse_dt(agora),
        aviso=AVISO_SEM_IA,
        motivo_desatualizacao=motivo,
        campos=campos,
    )


def get_ficha(conn: sqlite3.Connection, numero: str) -> AnaliseFicha:
    return ensure_ficha(conn, numero)


def update_campo(
    conn: sqlite3.Connection, numero: str, chave: str, body: AnaliseCampoUpdate
) -> AnaliseCampo:
    ficha = ensure_ficha(conn, numero)
    chaves = {c for c, _ in CAMPOS_FICHA}
    if chave not in chaves:
        raise ValueError(f"Campo desconhecido: {chave}")
    agora = _now()
    # Página opcional: TXT / sem páginas → não forçar número.
    pagina = body.pagina
    if body.documento_id and pagina is not None:
        mime = conn.execute(
            "SELECT tipo_mime FROM oportunidade_documentos WHERE id = ?",
            (body.documento_id,),
        ).fetchone()
        if mime:
            from otto_core.document_store import mime_exige_pagina

            if not mime_exige_pagina(str(mime["tipo_mime"] or "")):
                pagina = None
    cols = {r[1] for r in conn.execute("PRAGMA table_info(analise_campos)").fetchall()}
    # limpar_revisao True = revisão pelo usuário (nunca confirmação automática).
    if body.limpar_revisao and "revisao_origem" in cols:
        conn.execute(
            """
            UPDATE analise_campos
            SET valor = ?, natureza = ?, documento_id = ?, pagina = ?, trecho = ?,
                precisa_revisao = 0, revisao_origem = 'usuario', atualizado_em = ?
            WHERE ficha_id = ? AND chave = ?
            """,
            (
                body.valor,
                body.natureza,
                body.documento_id,
                pagina,
                body.trecho or "",
                agora,
                ficha.id,
                chave,
            ),
        )
    elif body.limpar_revisao:
        conn.execute(
            """
            UPDATE analise_campos
            SET valor = ?, natureza = ?, documento_id = ?, pagina = ?, trecho = ?,
                precisa_revisao = 0, atualizado_em = ?
            WHERE ficha_id = ? AND chave = ?
            """,
            (
                body.valor,
                body.natureza,
                body.documento_id,
                pagina,
                body.trecho or "",
                agora,
                ficha.id,
                chave,
            ),
        )
    else:
        conn.execute(
            """
            UPDATE analise_campos
            SET valor = ?, natureza = ?, documento_id = ?, pagina = ?, trecho = ?, atualizado_em = ?
            WHERE ficha_id = ? AND chave = ?
            """,
            (
                body.valor,
                body.natureza,
                body.documento_id,
                pagina,
                body.trecho or "",
                agora,
                ficha.id,
                chave,
            ),
        )
    conn.commit()
    ficha2 = ensure_ficha(conn, numero, preservar_desatualizada=False)
    for c in ficha2.campos:
        if c.chave == chave:
            return c
    raise ValueError(f"Campo não encontrado após atualização: {chave}")


def checklist_from_campo(
    conn: sqlite3.Connection, numero: str, chave: str
) -> ChecklistItem:
    ficha = ensure_ficha(conn, numero)
    campo = next((c for c in ficha.campos if c.chave == chave), None)
    if not campo:
        raise ValueError("Campo da ficha não encontrado.")
    titulo = f"Verificar: {campo.rotulo}"
    return add_checklist_item(
        conn,
        numero,
        ChecklistItemCreate(
            titulo=titulo,
            descricao=(campo.valor or "")[:500],
            requisito_chave=chave,
            categoria="requisito_ficha",
            evidencia_documento_id=campo.documento_id,
            evidencia_pagina=campo.pagina,
            evidencia_trecho=campo.trecho or "",
        ),
    )


def list_checklist(conn: sqlite3.Connection, numero: str) -> list[ChecklistItem]:
    rows = conn.execute(
        """
        SELECT * FROM checklist_itens
        WHERE numero_controle_pncp = ?
        ORDER BY id
        """,
        (numero,),
    ).fetchall()
    return [_row_checklist(r) for r in rows]


def add_checklist_item(
    conn: sqlite3.Connection, numero: str, body: ChecklistItemCreate
) -> ChecklistItem:
    opp = conn.execute(
        "SELECT 1 FROM oportunidades WHERE numero_controle_pncp = ?", (numero,)
    ).fetchone()
    if not opp:
        raise ValueError("Oportunidade não encontrada.")
    titulo = (body.titulo or "").strip()
    if not titulo:
        raise ValueError("Título do item é obrigatório.")
    agora = _now()
    cur = conn.execute(
        """
        INSERT INTO checklist_itens (
          numero_controle_pncp, titulo, descricao, status, requisito_chave,
          categoria, observacao, prazo_conhecido, responsavel,
          evidencia_documento_id, evidencia_pagina, evidencia_trecho, atualizado_em
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            numero,
            titulo,
            body.descricao or "",
            "pendente",
            body.requisito_chave or "",
            body.categoria or "",
            body.observacao or "",
            body.prazo_conhecido or "",
            body.responsavel or "",
            body.evidencia_documento_id,
            body.evidencia_pagina,
            body.evidencia_trecho or "",
            agora,
        ),
    )
    conn.commit()
    item = conn.execute("SELECT * FROM checklist_itens WHERE id = ?", (cur.lastrowid,)).fetchone()
    return _row_checklist(item)


def update_checklist_item(
    conn: sqlite3.Connection, numero: str, item_id: int, body: ChecklistItemUpdate
) -> ChecklistItem:
    row = conn.execute(
        "SELECT * FROM checklist_itens WHERE id = ? AND numero_controle_pncp = ?",
        (item_id, numero),
    ).fetchone()
    if not row:
        raise ValueError("Item de checklist não encontrado.")
    keys = _cols(row)
    agora = _now()
    titulo = body.titulo if body.titulo is not None else row["titulo"]
    descricao = body.descricao if body.descricao is not None else row["descricao"]
    status: StatusChecklist = body.status if body.status is not None else row["status"]
    req = body.requisito_chave if body.requisito_chave is not None else row["requisito_chave"]
    cat = (
        body.categoria
        if body.categoria is not None
        else ((row["categoria"] if "categoria" in keys else "") or "")
    )
    obs = (
        body.observacao
        if body.observacao is not None
        else ((row["observacao"] if "observacao" in keys else "") or "")
    )
    prazo = (
        body.prazo_conhecido
        if body.prazo_conhecido is not None
        else ((row["prazo_conhecido"] if "prazo_conhecido" in keys else "") or "")
    )
    resp = (
        body.responsavel
        if body.responsavel is not None
        else ((row["responsavel"] if "responsavel" in keys else "") or "")
    )
    ev_doc = (
        body.evidencia_documento_id
        if body.evidencia_documento_id is not None
        else row["evidencia_documento_id"]
    )
    ev_pag = (
        body.evidencia_pagina if body.evidencia_pagina is not None else row["evidencia_pagina"]
    )
    ev_trecho = (
        body.evidencia_trecho if body.evidencia_trecho is not None else row["evidencia_trecho"]
    )
    conn.execute(
        """
        UPDATE checklist_itens SET
          titulo=?, descricao=?, status=?, requisito_chave=?,
          categoria=?, observacao=?, prazo_conhecido=?, responsavel=?,
          evidencia_documento_id=?, evidencia_pagina=?, evidencia_trecho=?, atualizado_em=?
        WHERE id=?
        """,
        (
            titulo,
            descricao,
            status,
            req,
            cat,
            obs,
            prazo,
            resp,
            ev_doc,
            ev_pag,
            ev_trecho or "",
            agora,
            item_id,
        ),
    )
    conn.commit()
    return _row_checklist(
        conn.execute("SELECT * FROM checklist_itens WHERE id = ?", (item_id,)).fetchone()
    )
