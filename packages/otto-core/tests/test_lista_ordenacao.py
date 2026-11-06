from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from otto_core.db import get_cobertura_coleta, init_db, list_oportunidades


def _insert(conn: sqlite3.Connection, numero: str, pub: str | None, enc: str | None, nicho: str, score: float) -> None:
    conn.execute(
        """
        INSERT INTO oportunidades (
          numero_controle_pncp, orgao_razao_social, uf, objeto_compra, situacao,
          data_publicacao, data_encerramento, nicho, confianca_classificacao,
          score_total, score_detalhe, qualidade_dados, status_monitoramento, raw_json
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            numero,
            "Orgao Teste",
            "PI",
            f"Objeto {numero}",
            "Publicada",
            pub,
            enc,
            nicho,
            "alta" if nicho == "ti_software" else "nenhuma",
            score,
            json.dumps({"valor": 0, "urgencia": 0, "nicho": 0, "recorrencia": 0, "labels": {}}),
            "ok",
            "ativo",
            "{}",
        ),
    )


def test_lista_geral_sem_filtro_nicho_e_ordem_publicacao(tmp_path: Path):
    db = tmp_path / "t.db"
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    _insert(conn, "a", "2026-01-01T10:00:00", "2026-02-01T10:00:00", "outros", 99)
    _insert(conn, "b", "2026-03-01T10:00:00", "2026-04-01T10:00:00", "ti_software", 10)
    _insert(conn, "c", None, "2026-01-15T10:00:00", "outros", 50)
    conn.commit()

    items = list_oportunidades(conn, ordenacao="publicacao", limit=50)
    assert [i.numero_controle_pncp for i in items] == ["b", "a", "c"]
    assert {i.nicho for i in items} == {"outros", "ti_software"}
    conn.close()


def test_lista_ordem_prazo_sem_data_no_final(tmp_path: Path):
    db = tmp_path / "t.db"
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    _insert(conn, "sem", "2026-05-01T10:00:00", None, "outros", 80)
    _insert(conn, "longe", "2026-05-02T10:00:00", "2026-12-01T10:00:00", "outros", 80)
    _insert(conn, "perto", "2026-05-03T10:00:00", "2026-06-01T10:00:00", "ti_software", 5)
    conn.commit()

    items = list_oportunidades(conn, ordenacao="prazo", limit=50)
    assert [i.numero_controle_pncp for i in items] == ["perto", "longe", "sem"]
    conn.close()


def test_lista_filtro_ti_opcional(tmp_path: Path):
    db = tmp_path / "t.db"
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    _insert(conn, "ti", "2026-05-01T10:00:00", None, "ti_software", 1)
    _insert(conn, "out", "2026-05-02T10:00:00", None, "outros", 99)
    conn.commit()
    only_ti = list_oportunidades(conn, nicho="ti_software", ordenacao="publicacao")
    assert len(only_ti) == 1
    assert only_ti[0].numero_controle_pncp == "ti"
    conn.close()


def test_cobertura_aviso_e_ordenacao(tmp_path: Path):
    db = tmp_path / "t.db"
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    _insert(conn, "x", "2026-01-01T00:00:00", None, "outros", 1)
    conn.commit()

    # get_cobertura_coleta usa load_yaml real do projeto — ok se ingest.yaml existe
    cov = get_cobertura_coleta(conn)
    assert "Brasil" in cov["aviso"] or "brasil" in cov["aviso"].lower()
    assert cov["banco"]["total_oportunidades"] == 1
    assert cov["ordenacao"]["campo_prazo"] == "data_encerramento"
    assert cov["ordenacao"]["padrao"] == "publicacao"
    conn.close()
