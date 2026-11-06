from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from otto_core.db import init_db
from otto_core.orientacao_store import list_orientacao, upsert_orientacao


def test_orientacao_perguntas(tmp_path: Path):
    db = tmp_path / "o.db"
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    conn.execute(
        """
        INSERT INTO oportunidades (
          numero_controle_pncp, orgao_razao_social, uf, objeto_compra, situacao,
          data_publicacao, nicho, confianca_classificacao, score_total, score_detalhe,
          qualidade_dados, status_monitoramento, raw_json
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            "ORI-1",
            "ORG",
            "PI",
            "Obj",
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

    base = list_orientacao(conn, "ORI-1")
    assert len(base["items"]) >= 4
    assert all(i["resposta"] == "nao_respondida" for i in base["items"])

    out = upsert_orientacao(conn, "ORI-1", "local_prazo", "preciso_verificar", "conferir edital")
    item = next(i for i in out["items"] if i["id"] == "local_prazo")
    assert item["resposta"] == "preciso_verificar"
    assert item["detalhe"] == "conferir edital"
    conn.close()
