"""Aprendizado local a partir do histórico — só agregação, sem nuvem."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from otto_core.aprendizado_store import (
    MIN_DECISOES_PARA_INFLUENCIA,
    contexto_para_analise_ia,
    resumo_aprendizado,
)
from otto_core.auditoria_store import registrar
from otto_core.db import init_db


def _seed(conn: sqlite3.Connection, numero: str = "APR-1") -> None:
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


def test_resumo_vazio_e_honesto(tmp_path: Path, monkeypatch):
    db = tmp_path / "a.db"
    monkeypatch.setattr("otto_core.config.DB_PATH", db)
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    r = resumo_aprendizado(conn)
    assert r["nuvem"] is False
    assert r["altera_modelo"] is False
    assert r["influencia_prompt_local"] is True
    assert r["influencia_analise"]["ativa"] is False
    assert r["acoes"]["total"] == 0
    assert any("pouco histórico" in i.lower() or "pouco historico" in i.lower() for i in r["insights"])
    conn.close()


def test_resumo_com_auditoria_ia_e_resultado(tmp_path: Path, monkeypatch):
    db = tmp_path / "b.db"
    monkeypatch.setattr("otto_core.config.DB_PATH", db)
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    _seed(conn)

    registrar(conn, "salvar_acompanhamento", numero="APR-1", detalhe="salva=true")
    registrar(conn, "ia_sugestao_aplicada", numero="APR-1", detalhe="id=1")
    registrar(conn, "ia_sugestao_rejeitada", numero="APR-1", detalhe="id=2")

    # job mínimo + sugestões
    conn.execute(
        """
        INSERT INTO analise_ia_jobs (
          numero_controle_pncp, status, documento_ids_json, modelo,
          progresso, cobertura, erro, iniciado_em, atualizado_em
        ) VALUES (?,?,?,?,?,?,?,?,?)
        """,
        ("APR-1", "concluido", "[]", "qwen2.5:3b", "", "", "", "2026-11-06T00:00:00+00:00", "2026-11-06T00:00:00+00:00"),
    )
    job_id = int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])
    for estado, tipo, chave in (
        ("aplicada", "campo", "valores"),
        ("aplicada", "campo", "quantidades"),
        ("rejeitada", "campo", "objeto"),
        ("pendente", "requisito", ""),
    ):
        conn.execute(
            """
            INSERT INTO analise_ia_sugestoes (
              job_id, numero_controle_pncp, tipo, chave, titulo, valor,
              documento_id, pagina, trecho, referencia_confirmada, aviso_referencia,
              estado, criado_em
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                job_id,
                "APR-1",
                tipo,
                chave,
                chave or "req",
                "x",
                None,
                None,
                "trecho ok xx",
                1,
                "",
                estado,
                "2026-11-06T00:00:00+00:00",
            ),
        )

    conn.execute(
        """
        INSERT INTO oportunidade_fluxo (
          numero_controle_pncp, estado_fluxo, resultado_disputa, resultado_contratacao,
          resultado_execucao, resultado_recebimento, notas_resultado, atualizado_em
        ) VALUES (?,?,?,?,?,?,?,?)
        """,
        (
            "APR-1",
            "encerrada",
            "nao_vencemos",
            "nao_informado",
            "nao_informado",
            "nao_informado",
            "",
            "2026-11-06T00:00:00+00:00",
        ),
    )
    conn.commit()

    r = resumo_aprendizado(conn)
    assert r["acoes"]["total"] == 3
    assert r["ia_sugestoes"]["aplicadas"] == 2
    assert r["ia_sugestoes"]["rejeitadas"] == 1
    assert r["ia_sugestoes"]["pendentes"] == 1
    assert r["ia_sugestoes"]["taxa_aceitacao"] == round(2 / 3, 3)
    assert r["resultados"]["com_resultado"] == 1
    assert any("aceitação" in i.lower() or "aceitacao" in i.lower() for i in r["insights"])
    # 2 aplicadas + 1 rejeitada = 3 decisões → influência pode ativar
    assert r["ia_sugestoes"]["aplicadas"] + r["ia_sugestoes"]["rejeitadas"] >= MIN_DECISOES_PARA_INFLUENCIA
    ctx = contexto_para_analise_ia(conn)
    assert ctx["ativo"] is True
    assert "APRENDIZADO" not in ctx["bloco_prompt"]  # bloco sem tags; tags no job
    assert "Preferências do usuário" in ctx["bloco_prompt"]
    assert r["influencia_analise"]["ativa"] is True
    assert any("influência" in i.lower() or "influencia" in i.lower() for i in r["insights"])
    conn.close()


def test_contexto_inativo_com_poucas_decisoes(tmp_path: Path, monkeypatch):
    db = tmp_path / "c.db"
    monkeypatch.setattr("otto_core.config.DB_PATH", db)
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    _seed(conn, "APR-2")
    conn.execute(
        """
        INSERT INTO analise_ia_jobs (
          numero_controle_pncp, status, documento_ids_json, modelo,
          progresso, cobertura, erro, iniciado_em, atualizado_em
        ) VALUES (?,?,?,?,?,?,?,?,?)
        """,
        ("APR-2", "concluido", "[]", "qwen2.5:3b", "", "", "", "2026-11-06T00:00:00+00:00", "2026-11-06T00:00:00+00:00"),
    )
    job_id = int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])
    conn.execute(
        """
        INSERT INTO analise_ia_sugestoes (
          job_id, numero_controle_pncp, tipo, chave, titulo, valor,
          documento_id, pagina, trecho, referencia_confirmada, aviso_referencia,
          estado, criado_em
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            job_id, "APR-2", "campo", "valores", "Valores", "1",
            None, None, "trecho ok xx", 1, "", "aplicada", "2026-11-06T00:00:00+00:00",
        ),
    )
    conn.commit()
    ctx = contexto_para_analise_ia(conn)
    assert ctx["ativo"] is False
    assert ctx["decisoes"] == 1
    conn.close()


def test_chaves_evitar_quando_rejeitadas_dominam(tmp_path: Path, monkeypatch):
    db = tmp_path / "d.db"
    monkeypatch.setattr("otto_core.config.DB_PATH", db)
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    _seed(conn, "APR-3")
    conn.execute(
        """
        INSERT INTO analise_ia_jobs (
          numero_controle_pncp, status, documento_ids_json, modelo,
          progresso, cobertura, erro, iniciado_em, atualizado_em
        ) VALUES (?,?,?,?,?,?,?,?,?)
        """,
        ("APR-3", "concluido", "[]", "qwen2.5:3b", "", "", "", "2026-11-06T00:00:00+00:00", "2026-11-06T00:00:00+00:00"),
    )
    job_id = int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])
    for estado in ("rejeitada", "rejeitada", "aplicada"):
        conn.execute(
            """
            INSERT INTO analise_ia_sugestoes (
              job_id, numero_controle_pncp, tipo, chave, titulo, valor,
              documento_id, pagina, trecho, referencia_confirmada, aviso_referencia,
              estado, criado_em
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                job_id, "APR-3", "campo", "pendencias", "Pendências", "x",
                None, None, "trecho ok xx", 1, "", estado, "2026-11-06T00:00:00+00:00",
            ),
        )
    # mais uma aplicada em outra chave para completar decisões e preferida
    for _ in range(2):
        conn.execute(
            """
            INSERT INTO analise_ia_sugestoes (
              job_id, numero_controle_pncp, tipo, chave, titulo, valor,
              documento_id, pagina, trecho, referencia_confirmada, aviso_referencia,
              estado, criado_em
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                job_id, "APR-3", "campo", "quantidades", "Q", "200",
                None, None, "trecho ok xx", 1, "", "aplicada", "2026-11-06T00:00:00+00:00",
            ),
        )
    conn.commit()
    ctx = contexto_para_analise_ia(conn)
    assert ctx["ativo"] is True
    assert "pendencias" in ctx["chaves_evitar"]
    assert "quantidades" in ctx["chaves_preferidas"]
    conn.close()
