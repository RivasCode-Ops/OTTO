"""OCR local — lógica sem exigir Tesseract no CI."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from pypdf import PdfWriter

from otto_core.db import init_db
from otto_core.document_store import (
    adicionar_documento,
    formatos_info,
    list_paginas,
    reprocessar_extracao,
)
from otto_core.ocr_local import status_ocr


def _seed(conn: sqlite3.Connection, numero: str = "OCR-1") -> None:
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


def _pdf_sem_texto() -> bytes:
    """PDF com página em branco — pypdf não extrai texto útil."""
    w = PdfWriter()
    w.add_blank_page(width=200, height=200)
    import io

    buf = io.BytesIO()
    w.write(buf)
    return buf.getvalue()


def test_status_ocr_autorizado():
    st = status_ocr()
    assert st["autorizado"] is True
    assert st["nuvem"] is False
    assert "aviso" in st


def test_formatos_info_ocr_autorizado():
    info = formatos_info()
    assert info["ocr_autorizado"] is True
    assert "ocr" in info
    assert info["ocr"]["autorizado"] is True
    assert info["download_url_automatico"] is True


def test_pdf_sem_texto_com_ocr_mock(tmp_path: Path, monkeypatch):
    db = tmp_path / "o.db"
    docs = tmp_path / "documentos"
    monkeypatch.setattr("otto_core.config.DATA_DIR", tmp_path)
    monkeypatch.setattr("otto_core.config.DB_PATH", db)
    monkeypatch.setattr("otto_core.document_store.DOCUMENTOS_DIR", docs)

    monkeypatch.setattr(
        "otto_core.document_store.status_ocr",
        lambda: {
            "autorizado": True,
            "disponivel": True,
            "aviso": "mock",
            "nuvem": False,
        },
    )
    monkeypatch.setattr(
        "otto_core.document_store.ocr_pdf_para_paginas",
        lambda _path, so_paginas=None, escala=2.0: [(1, "Edital OCR teste quantidade 200")],
    )

    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    _seed(conn)

    doc = adicionar_documento(
        conn, "OCR-1", "scan.pdf", _pdf_sem_texto(), "application/pdf"
    )
    assert doc.status_extracao == "ok"
    assert "OCR" in (doc.aviso_extracao or "")
    pags = list_paginas(conn, doc.id)
    assert pags and "quantidade 200" in pags[0].texto
    conn.close()


def test_pdf_sem_texto_sem_motor_fica_ocr_necessario(tmp_path: Path, monkeypatch):
    db = tmp_path / "p.db"
    docs = tmp_path / "documentos"
    monkeypatch.setattr("otto_core.config.DATA_DIR", tmp_path)
    monkeypatch.setattr("otto_core.config.DB_PATH", db)
    monkeypatch.setattr("otto_core.document_store.DOCUMENTOS_DIR", docs)
    monkeypatch.setattr(
        "otto_core.document_store.status_ocr",
        lambda: {
            "autorizado": True,
            "disponivel": False,
            "aviso": "Falta Tesseract.",
            "nuvem": False,
        },
    )

    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    _seed(conn, "OCR-2")
    doc = adicionar_documento(
        conn, "OCR-2", "scan2.pdf", _pdf_sem_texto(), "application/pdf"
    )
    assert doc.status_extracao == "ocr_necessario"
    assert "Tesseract" in (doc.aviso_extracao or "") or "OCR" in (doc.aviso_extracao or "")
    conn.close()


def test_reprocessar_extracao_com_mock(tmp_path: Path, monkeypatch):
    db = tmp_path / "q.db"
    docs = tmp_path / "documentos"
    monkeypatch.setattr("otto_core.config.DATA_DIR", tmp_path)
    monkeypatch.setattr("otto_core.config.DB_PATH", db)
    monkeypatch.setattr("otto_core.document_store.DOCUMENTOS_DIR", docs)

    # 1ª vez: sem motor
    monkeypatch.setattr(
        "otto_core.document_store.status_ocr",
        lambda: {"autorizado": True, "disponivel": False, "aviso": "sem", "nuvem": False},
    )
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    _seed(conn, "OCR-3")
    doc = adicionar_documento(
        conn, "OCR-3", "scan3.pdf", _pdf_sem_texto(), "application/pdf"
    )
    assert doc.status_extracao == "ocr_necessario"

    # 2ª: motor mock
    monkeypatch.setattr(
        "otto_core.document_store.status_ocr",
        lambda: {"autorizado": True, "disponivel": True, "aviso": "ok", "nuvem": False},
    )
    monkeypatch.setattr(
        "otto_core.document_store.ocr_pdf_para_paginas",
        lambda *_a, **_k: [(1, "texto apos instalar tesseract")],
    )
    out = reprocessar_extracao(conn, doc.id)
    assert out.status_extracao == "ok"
    assert "texto apos" in list_paginas(conn, doc.id)[0].texto
    conn.close()
