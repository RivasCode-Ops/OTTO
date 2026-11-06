from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from otto_core.db import init_db
from otto_core.requisito_store import add_requisito, list_requisitos, update_requisito


def test_requisito_estados_sem_habilitacao(tmp_path: Path):
    db = tmp_path / "r.db"
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
            "REQ-1",
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

    item = add_requisito(conn, "REQ-1", "Certidão federal")
    assert item["estado"] == "nao_avaliado"
    item = update_requisito(conn, "REQ-1", item["id"], estado="evidencia_cadastrada")
    assert item["estado"] == "evidencia_cadastrada"
    out = list_requisitos(conn, "REQ-1")
    assert len(out["items"]) == 1
    assert "habilitação definitiva" in out["aviso"].lower() or "habilitacao" in out["aviso"].lower()
    assert "validado" in out["aviso"].lower()
    conn.close()
