"""Normalização / merge de órgãos (§12.1)."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from otto_core.db import init_db
from otto_core.orgaos_store import (
    get_orgao,
    list_orgaos,
    normalizar_cnpj,
    normalizar_nome_orgao,
    orgao_chave_de_row,
    resolver_orgao_chave,
    upsert_anotacao_orgao,
)


def test_normalizar_cnpj_mascara_e_digitos():
    assert normalizar_cnpj("12.345.678/0001-90") == "12345678000190"
    assert normalizar_cnpj("12345678000190") == "12345678000190"
    assert normalizar_cnpj("123") is None  # curto demais sem ser 11/14
    assert normalizar_cnpj("12345678") == "12345678"  # >=8 (teste / parcial)


def test_normalizar_nome_acentos():
    assert normalizar_nome_orgao("Prefeitura Municipal de Teresina") == normalizar_nome_orgao(
        "  PREFEITURA   MUNICIPAL DE TERESINA "
    )
    assert "A" in normalizar_nome_orgao("Órgão Á")


def test_merge_cnpj_mascarado_e_nome_sem_cnpj(tmp_path: Path):
    db = tmp_path / "n.db"
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    init_db(conn)

    cnpj_fmt = "12.345.678/0001-90"
    cnpj_dig = "12345678000190"
    nome = "Prefeitura Municipal de Teste"

    conn.execute(
        """
        INSERT INTO oportunidades (
          numero_controle_pncp, orgao_razao_social, uf, objeto_compra, situacao,
          data_publicacao, nicho, confianca_classificacao, score_total, score_detalhe,
          qualidade_dados, status_monitoramento, raw_json, valor_total_estimado
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            "N-1",
            nome,
            "PI",
            "Obj 1",
            "Publicada",
            "2026-01-01",
            "outros",
            "nenhuma",
            0,
            "{}",
            "ok",
            "ativo",
            json.dumps({"orgaoEntidade": {"cnpj": cnpj_fmt, "razaoSocial": nome}}),
            10,
        ),
    )
    # Mesmo nome, sem CNPJ no JSON — deve fundir
    conn.execute(
        """
        INSERT INTO oportunidades (
          numero_controle_pncp, orgao_razao_social, uf, objeto_compra, situacao,
          data_publicacao, nicho, confianca_classificacao, score_total, score_detalhe,
          qualidade_dados, status_monitoramento, raw_json, valor_total_estimado
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            "N-2",
            "PREFEITURA MUNICIPAL DE TESTE",
            "PI",
            "Obj 2",
            "Publicada",
            "2026-01-02",
            "outros",
            "nenhuma",
            0,
            "{}",
            "ok",
            "ativo",
            "{}",
            20,
        ),
    )
    # CNPJ só em unidadeOrgao
    conn.execute(
        """
        INSERT INTO oportunidades (
          numero_controle_pncp, orgao_razao_social, uf, objeto_compra, situacao,
          data_publicacao, nicho, confianca_classificacao, score_total, score_detalhe,
          qualidade_dados, status_monitoramento, raw_json, valor_total_estimado
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            "N-3",
            nome,
            "PI",
            "Obj 3",
            "Publicada",
            "2026-01-03",
            "outros",
            "nenhuma",
            0,
            "{}",
            "ok",
            "ativo",
            json.dumps(
                {
                    "orgaoEntidade": {"razaoSocial": nome},
                    "unidadeOrgao": {"cnpj": cnpj_dig},
                }
            ),
            30,
        ),
    )
    conn.commit()

    chave_fmt, c1, _ = orgao_chave_de_row(nome, json.dumps({"orgaoEntidade": {"cnpj": cnpj_fmt}}))
    assert c1 == cnpj_dig
    assert chave_fmt == f"cnpj:{cnpj_dig}"

    lista = list_orgaos(conn, limit=50)
    matches = [x for x in lista["items"] if x["cnpj"] == cnpj_dig]
    assert len(matches) == 1
    assert matches[0]["n_oportunidades"] == 3
    assert matches[0]["orgao_chave"] == f"cnpj:{cnpj_dig}"

    det = get_orgao(conn, f"cnpj:{cnpj_dig}")
    assert det is not None
    assert det["historico_disponivel"]["n_registros"] == 3

    # Anotação na chave antiga nome: deve aparecer após merge
    upsert_anotacao_orgao(
        conn,
        f"nome:{normalizar_nome_orgao(nome)}",
        "nota legado",
        nome=nome,
    )
    det2 = get_orgao(conn, f"cnpj:{cnpj_dig}")
    assert det2 is not None
    assert "nota legado" in det2["anotacoes"]

    conn.close()


def test_nao_funde_nomes_parecidos_sem_cnpj(tmp_path: Path):
    db = tmp_path / "p.db"
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    for i, nome in enumerate(["PREFEITURA DE ALFA", "PREF. MUNICIPAL DE ALFA"]):
        conn.execute(
            """
            INSERT INTO oportunidades (
              numero_controle_pncp, orgao_razao_social, uf, objeto_compra, situacao,
              data_publicacao, nicho, confianca_classificacao, score_total, score_detalhe,
              qualidade_dados, status_monitoramento, raw_json
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                f"P-{i}",
                nome,
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
            ),
        )
    conn.commit()
    lista = list_orgaos(conn, limit=50)
    assert lista["total"] == 2
    conn.close()


def test_resolver_usa_mapa(tmp_path: Path):
    mapa = {"ORGAO X": "99999999000199"}
    chave, cnpj, _ = resolver_orgao_chave("Órgão X", "{}", mapa)
    assert cnpj == "99999999000199"
    assert chave == "cnpj:99999999000199"
