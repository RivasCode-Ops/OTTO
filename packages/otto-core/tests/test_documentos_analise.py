from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from pypdf import PdfWriter

from otto_core.analise_store import (
    add_checklist_item,
    get_ficha,
    list_checklist,
    update_campo,
    update_checklist_item,
)
from otto_core.db import init_db, list_oportunidades, upsert_acompanhamento
from otto_core.document_store import (
    DocumentoErro,
    adicionar_documento,
    formatos_info,
    list_documentos,
    list_paginas,
)
from otto_core.models import (
    AcompanhamentoUpdate,
    AnaliseCampoUpdate,
    ChecklistItemCreate,
    ChecklistItemUpdate,
)


def _seed(conn: sqlite3.Connection, numero: str = "PNCP-DOC/1") -> None:
    conn.execute(
        """
        INSERT INTO oportunidades (
          numero_controle_pncp, orgao_razao_social, uf, objeto_compra, situacao,
          data_publicacao, nicho, confianca_classificacao, score_total, score_detalhe,
          qualidade_dados, status_monitoramento, raw_json, valor_total_estimado
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            numero,
            "Orgao Teste",
            "PI",
            "Objeto edital teste",
            "Publicada",
            "2026-01-10T12:00:00",
            "outros",
            "nenhuma",
            0,
            json.dumps({"valor": 0, "urgencia": 0, "nicho": 0, "recorrencia": 0, "labels": {}}),
            "ok",
            "ativo",
            "{}",
            1000.0,
        ),
    )
    conn.commit()


def test_formatos_info():
    info = formatos_info()
    assert ".pdf" in info["extensoes"]
    assert info["ocr_autorizado"] is True
    assert isinstance(info["ocr_disponivel"], bool)  # depende do Tesseract na máquina
    assert info["download_url_automatico"] is True
    # IA local depende do runtime na máquina (Ollama); não fixar False.
    assert isinstance(info["ia_analise_disponivel"], bool)
    assert info["ia_local"]["nuvem"] is False


def test_upload_versao_extracao_e_persistencia(tmp_path: Path, monkeypatch):
    db = tmp_path / "a.db"
    docs = tmp_path / "documentos"
    monkeypatch.setenv("OTTO_DATA_DIR", str(tmp_path))
    # Recarregar path do módulo
    import otto_core.document_store as ds
    import otto_core.config as cfg

    monkeypatch.setattr(cfg, "DATA_DIR", tmp_path)
    monkeypatch.setattr(cfg, "DB_PATH", db)
    monkeypatch.setattr(ds, "DOCUMENTOS_DIR", docs)
    docs.mkdir()

    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    _seed(conn)

    txt = b"Edital de teste pagina unica. Objeto: cadeiras."
    d1 = adicionar_documento(conn, "PNCP-DOC/1", "edital.txt", txt, "text/plain")
    assert d1.versao == 1
    assert d1.status_extracao == "ok"
    pags = list_paginas(conn, d1.id)
    assert len(pags) == 1 and "cadeiras" in pags[0].texto

    d2 = adicionar_documento(conn, "PNCP-DOC/1", "edital.txt", txt + b" v2", "text/plain")
    assert d2.versao == 2
    assert d2.documento_anterior_id == d1.id
    assert (docs / "PNCP-DOC_1" / d1.nome_armazenado).is_file()
    assert (docs / "PNCP-DOC_1" / d2.nome_armazenado).is_file()

    lista = list_documentos(conn, "PNCP-DOC/1")
    assert len(lista) == 2

    # PDF sem texto → ocr_necessario
    pdf_vazio = tmp_path / "vazio.pdf"
    w = PdfWriter()
    w.add_blank_page(width=200, height=200)
    w.write(pdf_vazio)
    raw_pdf = pdf_vazio.read_bytes()
    d3 = adicionar_documento(conn, "PNCP-DOC/1", "scan.pdf", raw_pdf, "application/pdf")
    assert d3.status_extracao == "ocr_necessario"

    # .doc legado continua rejeitado; bytes inválidos de "docx" falham na leitura
    try:
        adicionar_documento(conn, "PNCP-DOC/1", "x.doc", b"abc", "application/msword")
        assert False, "deveria rejeitar .doc"
    except DocumentoErro:
        pass

    conn.close()

    # Persistência em nova conexão
    conn2 = sqlite3.connect(db)
    conn2.row_factory = sqlite3.Row
    init_db(conn2)
    assert len(list_documentos(conn2, "PNCP-DOC/1")) == 3
    conn2.close()


def test_ficha_checklist_e_l2_preservado(tmp_path: Path, monkeypatch):
    db = tmp_path / "b.db"
    docs = tmp_path / "documentos"
    monkeypatch.setattr("otto_core.config.DATA_DIR", tmp_path)
    monkeypatch.setattr("otto_core.config.DB_PATH", db)
    monkeypatch.setattr("otto_core.document_store.DOCUMENTOS_DIR", docs)
    docs.mkdir()

    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    _seed(conn)

    upsert_acompanhamento(conn, "PNCP-DOC/1", AcompanhamentoUpdate(interesse=True, salva=True))

    ficha = get_ficha(conn, "PNCP-DOC/1")
    assert ficha.status == "aguardando_documentos"
    objeto = next(c for c in ficha.campos if c.chave == "objeto")
    assert objeto.natureza == "coleta"
    assert "edital teste" in objeto.valor.lower()

    adicionar_documento(conn, "PNCP-DOC/1", "a.txt", b"texto", "text/plain")
    ficha = get_ficha(conn, "PNCP-DOC/1")
    assert ficha.status == "parcial"

    update_campo(
        conn,
        "PNCP-DOC/1",
        "itens_lotes",
        AnaliseCampoUpdate(valor="Lote 1 — 10 unidades", natureza="usuario", trecho="manual"),
    )
    ficha = get_ficha(conn, "PNCP-DOC/1")
    assert ficha.status == "revisao_humana"

    item = add_checklist_item(
        conn,
        "PNCP-DOC/1",
        ChecklistItemCreate(titulo="Certidão negativa", requisito_chave="docs_requisitos"),
    )
    assert item.status == "pendente"
    item = update_checklist_item(
        conn,
        "PNCP-DOC/1",
        item.id,
        ChecklistItemUpdate(
            status="concluido",
            prazo_conhecido="2026-06-10",
            responsavel="Equipe local",
        ),
    )
    assert item.status == "concluido"
    assert item.prazo_conhecido == "2026-06-10"
    assert item.responsavel == "Equipe local"
    assert len(list_checklist(conn, "PNCP-DOC/1")) == 1

    # L2 intacto
    from otto_core.db import get_acompanhamento

    ac = get_acompanhamento(conn, "PNCP-DOC/1")
    assert ac.interesse and ac.salva
    assert len(list_oportunidades(conn, limit=10)) >= 1
    conn.close()
