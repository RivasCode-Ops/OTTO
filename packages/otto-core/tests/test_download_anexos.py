"""Download seletivo PNCP — mocks HTTP, sem rede real."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from otto_core.db import init_db
from otto_core.document_store import formatos_info, list_documentos
from otto_core.download_anexos_store import (
    DownloadAnexosErro,
    _url_permitida,
    baixar_anexos,
    listar_anexos_remotos,
    resolver_ids_compra,
)


def _seed(conn: sqlite3.Connection, numero: str = "12345678000190-2024-42") -> None:
    raw = {
        "orgaoEntidade": {"cnpj": "12.345.678/0001-90", "razaoSocial": "ORG"},
        "anoCompra": 2024,
        "sequencialCompra": 42,
        "objetoCompra": "Teste",
    }
    conn.execute(
        """
        INSERT INTO oportunidades (
          numero_controle_pncp, orgao_razao_social, uf, objeto_compra, situacao,
          data_publicacao, nicho, confianca_classificacao, score_total, score_detalhe,
          qualidade_dados, status_monitoramento, raw_json, origem_registro
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
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
            json.dumps(raw),
            "pncp",
        ),
    )
    conn.commit()


def test_url_whitelist():
    assert _url_permitida("https://pncp.gov.br/api/pncp/v1/orgaos/1/compras/2024/1/arquivos/1")
    assert not _url_permitida("http://pncp.gov.br/x")
    assert not _url_permitida("https://evil.example/x")
    assert not _url_permitida("https://user:pass@pncp.gov.br/x")


def test_formatos_download_flag():
    info = formatos_info()
    assert info["download_url_automatico"] is True
    assert "pncp.gov.br" in info["download_hosts"]


def test_resolver_ids(tmp_path: Path, monkeypatch):
    db = tmp_path / "a.db"
    monkeypatch.setattr("otto_core.config.DB_PATH", db)
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    _seed(conn)
    ids = resolver_ids_compra(conn, "12345678000190-2024-42")
    assert ids["cnpj"] == "12345678000190"
    assert ids["ano"] == 2024
    assert ids["sequencial"] == 42
    conn.close()


def test_listar_e_baixar_com_mock(tmp_path: Path, monkeypatch):
    db = tmp_path / "b.db"
    docs = tmp_path / "documentos"
    monkeypatch.setattr("otto_core.config.DATA_DIR", tmp_path)
    monkeypatch.setattr("otto_core.config.DB_PATH", db)
    monkeypatch.setattr("otto_core.document_store.DOCUMENTOS_DIR", docs)

    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    _seed(conn)

    def fake_json(_url: str):
        return [
            {
                "sequencialDocumento": 1,
                "titulo": "Edital.pdf",
                "tipoDocumentoNome": "Edital",
                "url": "https://pncp.gov.br/api/pncp/v1/orgaos/12345678000190/compras/2024/42/arquivos/1",
            },
            {
                "sequencialDocumento": 2,
                "titulo": "pacote.zip",
                "tipoDocumentoNome": "Anexo",
                "url": "https://pncp.gov.br/api/pncp/v1/orgaos/12345678000190/compras/2024/42/arquivos/2",
            },
            {
                "sequencialDocumento": 3,
                "titulo": "maligno",
                "tipoDocumentoNome": "X",
                "url": "https://evil.example/file.pdf",
            },
        ]

    lista = listar_anexos_remotos(conn, "12345678000190-2024-42", http_get=fake_json)
    assert len(lista["items"]) == 3
    assert lista["items"][0]["baixavel"] is True
    assert lista["items"][1]["baixavel"] is False  # zip
    assert lista["items"][2]["baixavel"] is False  # host

    pdf_bytes = b"%PDF-1.4 fake minimal content for upload test xxxxxxxxxx"

    def fake_bytes(url: str):
        assert "pncp.gov.br" in url
        return pdf_bytes, "application/pdf"

    # validar_upload precisa de extensão .pdf no nome — ok
    out = baixar_anexos(
        conn,
        "12345678000190-2024-42",
        http_get_json=fake_json,
        http_get_bytes=fake_bytes,
        max_arquivos=5,
    )
    assert len(out["baixados"]) == 1
    assert out["baixados"][0]["nome"].endswith(".pdf")
    docs_locais = list_documentos(conn, "12345678000190-2024-42")
    assert len(docs_locais) == 1
    assert docs_locais[0].origem == "download_pncp"

    # segunda vez: já local → não duplica
    out2 = baixar_anexos(
        conn,
        "12345678000190-2024-42",
        http_get_json=fake_json,
        http_get_bytes=fake_bytes,
    )
    assert out2["baixados"] == []
    conn.close()


def test_manual_sem_raw_falha(tmp_path: Path, monkeypatch):
    db = tmp_path / "c.db"
    monkeypatch.setattr("otto_core.config.DB_PATH", db)
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    conn.execute(
        """
        INSERT INTO oportunidades (
          numero_controle_pncp, orgao_razao_social, uf, objeto_compra, situacao,
          data_publicacao, nicho, confianca_classificacao, score_total, score_detalhe,
          qualidade_dados, status_monitoramento, raw_json, origem_registro
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            "MANUAL-X",
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
            "manual",
        ),
    )
    conn.commit()
    with pytest.raises(DownloadAnexosErro):
        listar_anexos_remotos(conn, "MANUAL-X", http_get=lambda u: [])
    conn.close()
