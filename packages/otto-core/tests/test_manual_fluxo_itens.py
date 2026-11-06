from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from otto_core.db import get_oportunidade, init_db, list_oportunidades
from otto_core.fluxo_store import update_fluxo
from otto_core.itens_lotes_store import add_item, add_lote, list_itens_lotes
from otto_core.manual_store import contagens_fluxo, criar_oportunidade_manual, listar_por_fluxo
from otto_core.models import FluxoUpdate


def test_manual_fluxo_itens_isolados_de_pncp(tmp_path: Path):
    db = tmp_path / "m.db"
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
            "PNCP-SEED/1",
            "ORG PNCP",
            "PI",
            "Objeto PNCP",
            "Publicada",
            "2026-01-01T10:00:00",
            "outros",
            "nenhuma",
            0,
            json.dumps({"valor": 0, "urgencia": 0, "nicho": 0, "recorrencia": 0, "labels": {}}),
            "ok",
            "ativo",
            "{}",
            "pncp",
        ),
    )
    conn.commit()

    man = criar_oportunidade_manual(
        conn,
        objeto_compra="Fornecimento de cadeiras",
        orgao_razao_social="Prefeitura Teste",
        uf="PI",
    )
    assert man.origem_registro == "manual"
    assert man.numero_controle_pncp.startswith("MANUAL-")

    lote = add_lote(conn, man.numero_controle_pncp, descricao="Lote 1")
    assert lote["disputa_separada_confirmada"] is False
    item = add_item(
        conn,
        man.numero_controle_pncp,
        descricao="Cadeira escolar",
        lote_id=lote["id"],
        quantidade=10,
        unidade="un",
    )
    assert item["lote_id"] == lote["id"]
    pack = list_itens_lotes(conn, man.numero_controle_pncp)
    assert "separadamente" in pack["aviso"].lower() or "disput" in pack["aviso"].lower()

    update_fluxo(conn, man.numero_controle_pncp, FluxoUpdate(estado_fluxo="arquivada"))
    gerais = list_oportunidades(conn, excluir_arquivadas=True)
    assert all(o.numero_controle_pncp != man.numero_controle_pncp for o in gerais)
    arq = listar_por_fluxo(conn, "arquivada")
    assert any(x["oportunidade"].numero_controle_pncp == man.numero_controle_pncp for x in arq)
    assert contagens_fluxo(conn)["arquivada"] >= 1

    # PNCP permanece
    assert get_oportunidade(conn, "PNCP-SEED/1") is not None
    conn.close()
