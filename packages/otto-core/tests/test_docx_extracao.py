"""DOCX — extração local autorizada 2026-11-06."""
from __future__ import annotations

import io
import json
import sqlite3
from pathlib import Path

from docx import Document

from otto_core.db import init_db
from otto_core.document_store import (
    DocumentoErro,
    MIME_DOCX,
    adicionar_documento,
    formatos_info,
    list_paginas,
    mime_exige_pagina,
)


def _seed(conn: sqlite3.Connection, numero: str = "DOCX-1") -> None:
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
            "Obj",
            "Publicada",
            "2026-01-01",
            "outros",
            "nenhuma",
            0,
            "{}",
            "ok",
            "ativo",
            "{}",
        ),
    )
    conn.commit()


def _docx_bytes(texto: str = "Objeto: cadeiras 200 unidades") -> bytes:
    doc = Document()
    doc.add_paragraph(texto)
    table = doc.add_table(rows=1, cols=2)
    table.rows[0].cells[0].text = "Item"
    table.rows[0].cells[1].text = "Quantidade 200"
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def test_formatos_inclui_docx():
    info = formatos_info()
    assert ".docx" in info["extensoes"]
    assert info["docx"] is True
    assert mime_exige_pagina(MIME_DOCX) is False
    assert mime_exige_pagina("application/pdf") is True


def test_upload_docx_extrai_texto(tmp_path: Path, monkeypatch):
    db = tmp_path / "d.db"
    docs = tmp_path / "documentos"
    monkeypatch.setattr("otto_core.config.DATA_DIR", tmp_path)
    monkeypatch.setattr("otto_core.config.DB_PATH", db)
    monkeypatch.setattr("otto_core.document_store.DOCUMENTOS_DIR", docs)

    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    _seed(conn)

    meta = adicionar_documento(
        conn, "DOCX-1", "edital.docx", _docx_bytes(), MIME_DOCX
    )
    assert meta.status_extracao == "ok"
    assert "DOCX" in (meta.aviso_extracao or "")
    pags = list_paginas(conn, meta.id)
    assert len(pags) == 1
    assert "cadeiras" in pags[0].texto
    assert "Quantidade 200" in pags[0].texto
    conn.close()


def test_rejeita_doc_legado(tmp_path: Path, monkeypatch):
    db = tmp_path / "e.db"
    docs = tmp_path / "documentos"
    monkeypatch.setattr("otto_core.config.DATA_DIR", tmp_path)
    monkeypatch.setattr("otto_core.config.DB_PATH", db)
    monkeypatch.setattr("otto_core.document_store.DOCUMENTOS_DIR", docs)
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    _seed(conn, "DOCX-2")
    try:
        adicionar_documento(
            conn, "DOCX-2", "antigo.doc", b"nao e docx", "application/msword"
        )
        assert False, "deveria rejeitar .doc"
    except DocumentoErro:
        pass
    conn.close()
