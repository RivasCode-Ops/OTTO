"""Evidência com versão/página/trecho + sinalização de revisão (sem atualizar vínculo)."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from otto_core.analise_store import (
    confirmar_revisao_ficha,
    get_ficha,
    update_campo,
)
from otto_core.db import init_db
from otto_core.document_store import adicionar_documento
from otto_core.models import AnaliseCampoUpdate
from otto_core.requisito_store import (
    add_requisito,
    checklist_from_requisito,
    list_requisitos,
    update_requisito,
)


def _seed(conn: sqlite3.Connection, numero: str = "EVID-1") -> None:
    conn.execute(
        """
        INSERT INTO oportunidades (
          numero_controle_pncp, orgao_razao_social, uf, objeto_compra, situacao,
          data_publicacao, nicho, confianca_classificacao, score_total, score_detalhe,
          qualidade_dados, status_monitoramento, raw_json
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            numero,
            "ORG",
            "PI",
            "Obj evidência",
            "Publicada",
            "2026-01-01",
            "outros",
            "nenhuma",
            0,
            json.dumps({"valor": 0, "urgencia": 0, "nicho": 0, "recorrencia": 0, "labels": {}}),
            "ok",
            "ativo",
            "{}",
        ),
    )
    conn.commit()


def test_evidencia_pagina_txt_e_revisao_por_versao(tmp_path: Path, monkeypatch):
    db = tmp_path / "e.db"
    docs = tmp_path / "documentos"
    monkeypatch.setattr("otto_core.config.DATA_DIR", tmp_path)
    monkeypatch.setattr("otto_core.config.DB_PATH", db)
    monkeypatch.setattr("otto_core.document_store.DOCUMENTOS_DIR", docs)
    docs.mkdir()

    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    _seed(conn)

    # Migração 011 deve existir após init_db.
    cols = {r[1] for r in conn.execute("PRAGMA table_info(requisitos_verificacao)").fetchall()}
    assert "evidencia_pagina" in cols
    assert "precisa_revisao" in cols
    assert "revisao_origem" in cols

    d1 = adicionar_documento(
        conn, "EVID-1", "edital.txt", b"Texto do edital certidao federal.", "text/plain"
    )
    assert d1.versao == 1

    # Campo da ficha: TXT sem inventar página (mesmo se tentar enviar).
    update_campo(
        conn,
        "EVID-1",
        "docs_requisitos",
        AnaliseCampoUpdate(
            valor="Certidão federal",
            natureza="usuario",
            documento_id=d1.id,
            pagina=3,
            trecho="certidao federal",
        ),
    )
    ficha = get_ficha(conn, "EVID-1")
    campo = next(c for c in ficha.campos if c.chave == "docs_requisitos")
    assert campo.documento_id == d1.id
    assert campo.pagina is None
    assert "certidao" in campo.trecho.lower()

    req = add_requisito(conn, "EVID-1", "Certidão federal negativa")
    req = update_requisito(
        conn,
        "EVID-1",
        req["id"],
        estado="evidencia_cadastrada",
        evidencia_documento_id=d1.id,
        evidencia_pagina=9,  # deve zerar para TXT
        evidencia_trecho="certidao federal",
    )
    assert req["evidencia_documento_id"] == d1.id
    assert req["evidencia_pagina"] is None
    assert req["precisa_revisao"] is False
    assert req["revisao_origem"] == "usuario"
    assert req["evidencia_documento"]["versao"] == 1
    assert req["evidencia_documento"]["pagina_aplicavel"] is False

    tarefa = checklist_from_requisito(conn, "EVID-1", req["id"])
    assert tarefa.requisito_chave == f"requisito:{req['id']}"
    assert tarefa.evidencia_documento_id == d1.id
    assert tarefa.evidencia_pagina is None

    # Nova versão: não altera vínculo antigo; sinaliza revisão.
    d2 = adicionar_documento(
        conn, "EVID-1", "edital.txt", b"Texto do edital v2 certidao.", "text/plain"
    )
    assert d2.versao == 2
    assert d2.documento_anterior_id == d1.id

    ficha2 = get_ficha(conn, "EVID-1")
    assert ficha2.status == "desatualizada"
    campo2 = next(c for c in ficha2.campos if c.chave == "docs_requisitos")
    assert campo2.precisa_revisao is True
    assert campo2.documento_id == d1.id  # vínculo antigo preservado
    assert campo2.pagina is None

    pack = list_requisitos(conn, "EVID-1")
    r2 = next(i for i in pack["items"] if i["id"] == req["id"])
    assert r2["precisa_revisao"] is True
    assert r2["evidencia_documento_id"] == d1.id
    assert r2["revisao_origem"] == ""

    # Confirmação pelo usuário — nunca automática.
    confirmar_revisao_ficha(conn, "EVID-1")
    ficha3 = get_ficha(conn, "EVID-1")
    assert ficha3.status != "desatualizada"
    campo3 = next(c for c in ficha3.campos if c.chave == "docs_requisitos")
    assert campo3.precisa_revisao is False
    assert campo3.revisao_origem == "usuario"
    assert campo3.documento_id == d1.id

    pack2 = list_requisitos(conn, "EVID-1")
    r3 = next(i for i in pack2["items"] if i["id"] == req["id"])
    assert r3["precisa_revisao"] is False
    assert r3["revisao_origem"] == "usuario"
    assert r3["evidencia_documento_id"] == d1.id

    # Registro antigo sem página: permanece NULL (não inventar).
    conn.execute(
        """
        INSERT INTO requisitos_verificacao (
          numero_controle_pncp, descricao, origem, estado,
          evidencia_documento_id, evidencia_pagina, evidencia_trecho,
          precisa_revisao, revisao_origem, observacao, atualizado_em
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            "EVID-1",
            "Requisito legado",
            "usuario",
            "evidencia_cadastrada",
            d1.id,
            None,
            "legado",
            0,
            "",
            "",
            "2026-01-01T00:00:00+00:00",
        ),
    )
    conn.commit()
    legado = next(i for i in list_requisitos(conn, "EVID-1")["items"] if i["descricao"] == "Requisito legado")
    assert legado["evidencia_pagina"] is None

    conn.close()


def test_evidencia_pagina_pdf_persistida(tmp_path: Path, monkeypatch):
    from pypdf import PdfWriter
    from io import BytesIO

    db = tmp_path / "p.db"
    docs = tmp_path / "documentos"
    monkeypatch.setattr("otto_core.config.DATA_DIR", tmp_path)
    monkeypatch.setattr("otto_core.config.DB_PATH", db)
    monkeypatch.setattr("otto_core.document_store.DOCUMENTOS_DIR", docs)
    docs.mkdir()

    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    _seed(conn, "EVID-PDF")

    buf = BytesIO()
    w = PdfWriter()
    w.add_blank_page(width=200, height=200)
    w.write(buf)
    d = adicionar_documento(
        conn, "EVID-PDF", "edital.pdf", buf.getvalue(), "application/pdf"
    )
    req = add_requisito(conn, "EVID-PDF", "Habilitação jurídica")
    req = update_requisito(
        conn,
        "EVID-PDF",
        req["id"],
        evidencia_documento_id=d.id,
        evidencia_pagina=1,
        evidencia_trecho="clausula 5.1",
        estado="evidencia_cadastrada",
    )
    assert req["evidencia_pagina"] == 1
    assert req["evidencia_documento"]["pagina_aplicavel"] is True
    conn.close()
