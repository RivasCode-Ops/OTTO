from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from otto_core.db import init_db
from otto_core.orgaos_store import (
    add_classificacao,
    concorrencia_status,
    ensure_classificacoes_basicas,
    get_orgao,
    indicadores_explorar,
    list_classificacoes_opp,
    list_orgaos,
    visao_categorias,
    visao_regiao,
)


def _seed(conn: sqlite3.Connection) -> None:
    raw = json.dumps(
        {
            "orgaoEntidade": {"cnpj": "12.345.678/0001-23", "razaoSocial": "ORGAO A"},
            "unidadeOrgao": {"municipioNome": "Teresina", "ufSigla": "PI"},
        }
    )
    for i, (nome, uf, nicho) in enumerate(
        [
            ("ORGAO A", "PI", "ti_software"),
            ("ORGAO A", "PI", "outros"),
            ("ORGAO B", "SP", "outros"),
        ]
    ):
        conn.execute(
            """
            INSERT INTO oportunidades (
              numero_controle_pncp, orgao_razao_social, uf, objeto_compra, situacao,
              data_publicacao, nicho, confianca_classificacao, score_total, score_detalhe,
              qualidade_dados, status_monitoramento, raw_json, valor_total_estimado
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                f"ORG-{i}",
                nome,
                uf,
                f"Objeto {i}",
                "Publicada",
                "2026-01-10T12:00:00",
                nicho,
                "nenhuma",
                0,
                json.dumps({"valor": 0, "urgencia": 0, "nicho": 0, "recorrencia": 0, "labels": {}}),
                "ok",
                "ativo",
                raw if nome == "ORGAO A" else "{}",
                100.0 * (i + 1),
            ),
        )
    conn.commit()


def test_orgaos_categorias_concorrencia_insuficiente(tmp_path: Path):
    db = tmp_path / "o.db"
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    _seed(conn)

    n = ensure_classificacoes_basicas(conn)
    assert n >= 3

    lista = list_orgaos(conn, limit=50)
    assert lista["total"] >= 2
    assert all("n_oportunidades" in x for x in lista["items"])

    chave = next(x["orgao_chave"] for x in lista["items"] if x["cnpj"] == "12345678000123")
    det = get_orgao(conn, chave)
    assert det is not None
    assert det["historico_disponivel"]["n_registros"] >= 1

    add_classificacao(conn, "ORG-0", setor="saude", categoria="materiais")
    cats = visao_categorias(conn)
    # Visão Categorias agrega oportunidades.nicho (não só tabela de classificações).
    assert any(c.get("nicho") or c["setor"] for c in cats["items"])
    assert any(
        (c.get("nicho") or c["setor"]) in ("ti_software", "outros", "saude_medicamentos")
        for c in cats["items"]
    )
    assert list_classificacoes_opp(conn, "ORG-0")

    regs = visao_regiao(conn)
    assert {r["uf"] for r in regs["items"]} >= {"PI", "SP"}

    ind = indicadores_explorar(conn)
    assert ind["total_oportunidades"] == 3
    assert "Base" in ind["base_calculo"] or "base" in ind["base_calculo"].lower() or "SQLite" in ind["base_calculo"]
    assert any("concorrência" in l.lower() or "participantes" in l.lower() for l in ind["limitacoes"])

    conc = concorrencia_status(conn)
    assert conc["dados_suficientes"] is False
    assert conc["mensagem"] == "Dados insuficientes"
    assert conc["integracao_faltante"]
    assert "editais" not in (conc["detalhe"] or "").lower() or "NÃO" in (conc["detalhe"] or "")

    conn.close()
