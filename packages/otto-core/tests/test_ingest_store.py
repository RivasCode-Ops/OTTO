"""Coleta PNCP via core — sem rede real."""
from __future__ import annotations

import sqlite3
import time
from pathlib import Path

import pytest

from otto_core.db import init_db
from otto_core.ingest_store import (
    IngestEmAndamentoError,
    IngestParamsError,
    executar_coleta,
    iniciar_coleta_async,
    status_coleta,
)


def _raw(numero: str = "INGEST-TEST-1") -> dict:
    return {
        "numeroControlePNCP": numero,
        "objetoCompra": "Serviço de teste ingest",
        "orgaoEntidade": {"razaoSocial": "ORGAO TESTE"},
        "unidadeOrgao": {"ufSigla": "PI"},
        "situacaoCompraNome": "Divulgada no PNCP",
        "dataPublicacaoPncp": "2026-11-01T10:00:00",
        "valorTotalEstimado": 1000,
        "codigoModalidadeContratacao": 6,
    }


def test_executar_coleta_com_mock(tmp_path: Path, monkeypatch):
    db = tmp_path / "i.db"
    monkeypatch.setattr("otto_core.config.DB_PATH", db)
    monkeypatch.setattr("otto_core.ingest_store.get_connection", lambda: _conn(db))

    def fake_collect(**_kwargs):
        return [_raw("INGEST-A"), _raw("INGEST-A"), _raw("INGEST-B")]

    out = executar_coleta(days=2, uf="pi", collect_fn=fake_collect)
    assert out["status"] == "ok"
    assert out["total_bruto"] == 3
    assert out["total_novos"] == 2
    assert out["total_atualizados"] == 1
    assert out["erros"] == 0

    conn = _conn(db)
    st = status_coleta(conn)
    assert st["em_andamento"] is False
    assert st["ultima_execucao"]["mensagem"] == "ok"
    assert st["ultima_execucao"]["total_novos"] == 2
    n = conn.execute("SELECT COUNT(*) AS c FROM oportunidades").fetchone()["c"]
    assert n == 2
    conn.close()


def test_params_invalidos(tmp_path: Path, monkeypatch):
    db = tmp_path / "j.db"
    monkeypatch.setattr("otto_core.config.DB_PATH", db)
    monkeypatch.setattr("otto_core.ingest_store.get_connection", lambda: _conn(db))
    with pytest.raises(IngestParamsError):
        executar_coleta(days=99, collect_fn=lambda **_: [])
    with pytest.raises(IngestParamsError):
        executar_coleta(days=7, uf="PIA", collect_fn=lambda **_: [])


def test_bloqueia_segunda_coleta_em_andamento(tmp_path: Path, monkeypatch):
    db = tmp_path / "k.db"
    monkeypatch.setattr("otto_core.config.DB_PATH", db)
    monkeypatch.setattr("otto_core.ingest_store.get_connection", lambda: _conn(db))

    conn = _conn(db)
    conn.execute(
        """
        INSERT INTO ingest_runs (iniciado_em, ufs, data_inicial, data_final, mensagem)
        VALUES (datetime('now'), 'PI', '2026-11-01', '2026-11-06', 'em_andamento')
        """
    )
    conn.commit()
    conn.close()

    with pytest.raises(IngestEmAndamentoError):
        executar_coleta(days=2, collect_fn=lambda **_: [])


def test_iniciar_async_e_conclui(tmp_path: Path, monkeypatch):
    db = tmp_path / "l.db"
    monkeypatch.setattr("otto_core.config.DB_PATH", db)
    monkeypatch.setattr("otto_core.ingest_store.get_connection", lambda: _conn(db))

    def fake_collect(**_kwargs):
        return [_raw("INGEST-ASYNC-1")]

    # Patch worker path
    import otto_core.ingest_store as mod

    orig = mod._executar_run_existente

    def wrapped(conn, run_id, *, days, uf, collect_fn=None):
        return orig(conn, run_id, days=days, uf=uf, collect_fn=fake_collect)

    monkeypatch.setattr(mod, "_executar_run_existente", wrapped)

    started = iniciar_coleta_async(days=2, uf="PI")
    assert started["status"] == "em_andamento"
    assert started["id"] > 0

    # aguarda worker
    deadline = time.time() + 5
    while time.time() < deadline:
        conn = _conn(db)
        st = status_coleta(conn)
        conn.close()
        if not st["em_andamento"] and st["ultima_execucao"] and st["ultima_execucao"]["finalizado_em"]:
            break
        time.sleep(0.05)
    else:
        pytest.fail("coleta async não finalizou")

    conn = _conn(db)
    st = status_coleta(conn)
    assert st["em_andamento"] is False
    assert st["ultima_execucao"]["mensagem"] == "ok"
    assert st["ultima_execucao"]["total_novos"] == 1
    conn.close()


def test_coleta_nacional_persiste_mesmo_com_uf_falha(tmp_path: Path, monkeypatch):
    """Uma UF com erro de rede não descarta as UFs já gravadas."""
    db = tmp_path / "nacional.db"
    monkeypatch.setattr("otto_core.config.DB_PATH", db)
    monkeypatch.setattr("otto_core.ingest_store.get_connection", lambda: _conn(db))
    monkeypatch.setattr(
        "otto_core.ingest_store.load_yaml",
        lambda _name: {"ufs": ["PI", "AL", "CE"], "modalidades": [6], "janela_dias_padrao": 7},
    )

    class FakeClient:
        def __init__(self, _cfg):
            pass

        def collect_window(self, days=None, ufs=None, modalidades=None):
            uf = (ufs or ["PI"])[0]
            if uf == "AL":
                raise RuntimeError("PNCP 429 simulado")
            return [
                {
                    **_raw(f"INGEST-{uf}-1"),
                    "unidadeOrgao": {"ufSigla": uf},
                }
            ]

    monkeypatch.setattr("otto_core.ingest_store.PncpClient", FakeClient)

    out = executar_coleta(days=2)
    assert out["status"] == "ok_parcial"
    assert out["total_novos"] == 2
    assert any(f.startswith("AL:") for f in out["falhas_uf"])

    conn = _conn(db)
    ufs = {
        r["uf"]
        for r in conn.execute("SELECT DISTINCT uf FROM oportunidades")
    }
    assert ufs == {"PI", "CE"}
    assert conn.execute(
        "SELECT mensagem FROM ingest_runs ORDER BY id DESC LIMIT 1"
    ).fetchone()["mensagem"].startswith("ok_parcial")
    conn.close()


def _conn(db: Path) -> sqlite3.Connection:
    c = sqlite3.connect(db)
    c.row_factory = sqlite3.Row
    init_db(c)
    return c
