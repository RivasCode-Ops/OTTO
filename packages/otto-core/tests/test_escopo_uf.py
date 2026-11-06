"""Escopo UF: lista/KPIs filtram UFs da coleta; histórico de outras UFs permanece."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from otto_core.db import (
    count_oportunidades,
    init_db,
    kpis,
    list_oportunidades,
    resolver_ufs_filtro,
)


def _insert(conn: sqlite3.Connection, numero: str, uf: str) -> None:
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
            uf,
            f"Obj {numero}",
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


def test_resolver_ufs_filtro_padrao_config(monkeypatch):
    monkeypatch.setattr(
        "otto_core.db.ufs_da_coleta_config", lambda: ["PI"]
    )
    assert resolver_ufs_filtro(escopo_uf="config") == ["PI"]
    assert resolver_ufs_filtro(escopo_uf="todas") is None
    assert resolver_ufs_filtro(uf="SP", escopo_uf="config") == ["SP"]


def test_lista_e_kpi_filtram_uf(tmp_path: Path):
    db = tmp_path / "u.db"
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    _insert(conn, "pi-1", "PI")
    _insert(conn, "sp-1", "SP")
    _insert(conn, "sp-2", "SP")
    conn.commit()

    assert count_oportunidades(conn, ufs=["PI"]) == 1
    assert count_oportunidades(conn, ufs=None) == 3
    items = list_oportunidades(conn, ufs=["PI"], limit=50)
    assert [i.numero_controle_pncp for i in items] == ["pi-1"]

    k = kpis(conn, ufs=["PI"])
    assert k["total"] == 1
    k_all = kpis(conn, ufs=None)
    assert k_all["total"] == 3
    conn.close()
