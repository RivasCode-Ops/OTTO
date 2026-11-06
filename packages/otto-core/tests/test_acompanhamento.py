from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from otto_core.db import (
    contagens_acompanhamento,
    get_acompanhamento,
    init_db,
    list_acompanhamento,
    list_oportunidades,
    upsert_acompanhamento,
)
from otto_core.fluxo_store import get_fluxo, update_fluxo
from otto_core.migrations import apply_migrations
from otto_core.models import AcompanhamentoUpdate, FluxoUpdate
from otto_core.orgaos_store import add_classificacao


def _seed(conn: sqlite3.Connection, numero: str = "PNCP-1") -> None:
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
            "Orgao",
            "PI",
            "Objeto teste",
            "Publicada",
            "2026-01-10T12:00:00",
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


def test_migracao_idempotente(tmp_path: Path):
    db = tmp_path / "a.db"
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    again = apply_migrations(conn)
    assert again == []
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert "oportunidade_acompanhamento" in tables
    assert "schema_migrations" in tables
    conn.close()


def test_salvar_desfazer_interesse_decisao_persistencia(tmp_path: Path):
    db = tmp_path / "a.db"
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    _seed(conn)

    a = upsert_acompanhamento(conn, "PNCP-1", AcompanhamentoUpdate(salva=True))
    assert a.salva is True
    a = upsert_acompanhamento(conn, "PNCP-1", AcompanhamentoUpdate(salva=False, interesse=True))
    assert a.salva is False and a.interesse is True
    a = upsert_acompanhamento(
        conn,
        "PNCP-1",
        AcompanhamentoUpdate(
            decisao="prosseguir",
            justificativa="vale analisar",
            observacoes="nota 1",
        ),
    )
    assert a.decisao == "prosseguir"
    assert a.justificativa == "vale analisar"

    # Reabre conexão = “reinício”
    conn.close()
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    salvo = get_acompanhamento(conn, "PNCP-1")
    assert salvo.interesse is True
    assert salvo.decisao == "prosseguir"
    assert salvo.observacoes == "nota 1"

    counts = contagens_acompanhamento(conn)
    assert counts["interesse"] == 1
    assert counts["prosseguir"] == 1
    assert counts["salvas"] == 0

    lista = list_acompanhamento(conn, filtro="prosseguir")
    assert len(lista) == 1
    assert lista[0]["oportunidade"].numero_controle_pncp == "PNCP-1"

    upsert_acompanhamento(conn, "PNCP-1", AcompanhamentoUpdate(decisao="nao_prosseguir"))
    assert get_acompanhamento(conn, "PNCP-1").decisao == "nao_prosseguir"
    assert len(list_acompanhamento(conn, filtro="nao_prosseguir")) == 1
    conn.close()


def test_lista_geral_ainda_funciona_apos_migracao(tmp_path: Path):
    db = tmp_path / "a.db"
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    _seed(conn, "A")
    _seed(conn, "B")
    items = list_oportunidades(conn, ordenacao="publicacao")
    assert len(items) == 2
    conn.close()


def test_salvar_sincroniza_estado_fluxo_salva(tmp_path: Path):
    db = tmp_path / "sync.db"
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    _seed(conn, "PNCP-SYNC")
    assert get_fluxo(conn, "PNCP-SYNC").estado_fluxo == "nao_avaliada"
    upsert_acompanhamento(conn, "PNCP-SYNC", AcompanhamentoUpdate(salva=True))
    assert get_fluxo(conn, "PNCP-SYNC").estado_fluxo == "salva"
    # Não rebaixa fluxo avançado
    update_fluxo(conn, "PNCP-SYNC", FluxoUpdate(estado_fluxo="em_analise"))
    upsert_acompanhamento(conn, "PNCP-SYNC", AcompanhamentoUpdate(salva=True))
    assert get_fluxo(conn, "PNCP-SYNC").estado_fluxo == "em_analise"
    conn.close()


def test_lista_enriquece_categoria_e_docs(tmp_path: Path):
    db = tmp_path / "enr.db"
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    _seed(conn, "PNCP-ENR")
    add_classificacao(conn, "PNCP-ENR", setor="ti", categoria="software")
    items = list_oportunidades(conn, ordenacao="publicacao")
    one = next(o for o in items if o.numero_controle_pncp == "PNCP-ENR")
    assert one.categoria_principal == "software"
    assert one.documentos_count == 0
    conn.close()
