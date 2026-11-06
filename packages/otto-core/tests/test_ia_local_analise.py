"""IA local: validação de citação, preservação de dados, indisponibilidade sem mock de modelo."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from otto_core.analise_store import get_ficha, update_campo
from otto_core.db import init_db
from otto_core.document_store import adicionar_documento
from otto_core.ia_analise_store import (
    aplicar_sugestao,
    avaliar_referencia_sugestao,
    iniciar_analise,
    listar_sugestoes,
    localizar_citacao_no_documento,
    rejeitar_sugestao,
    trecho_confirmado_no_texto,
)
from otto_core.ia_local_runtime import IaLocalErro, _assert_loopback, status_runtime
from otto_core.models import AnaliseCampoUpdate


def _seed(conn: sqlite3.Connection, numero: str = "IA-1") -> None:
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
            "Obj IA",
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


def test_somente_loopback():
    assert _assert_loopback("http://127.0.0.1:11434").endswith("11434")
    try:
        _assert_loopback("https://api.openai.com/v1")
        assert False, "deveria recusar nuvem"
    except IaLocalErro:
        pass


def test_trecho_confirmado():
    ok, _ = trecho_confirmado_no_texto(
        "certidao federal negativa",
        ["Edital exige certidao federal negativa para habilitacao."],
    )
    assert ok is True
    ok2, aviso = trecho_confirmado_no_texto("texto inventado xyzzy", ["apenas outro conteudo"])
    assert ok2 is False
    assert "não encontrado" in aviso.lower() or "nao encontrado" in aviso.lower()


def test_job_falha_sem_runtime_e_preserva_usuario(tmp_path: Path, monkeypatch):
    db = tmp_path / "ia.db"
    docs = tmp_path / "documentos"
    monkeypatch.setattr("otto_core.config.DATA_DIR", tmp_path)
    monkeypatch.setattr("otto_core.config.DB_PATH", db)
    monkeypatch.setattr("otto_core.document_store.DOCUMENTOS_DIR", docs)
    docs.mkdir()

    # Força runtime indisponível (porta improvável)
    monkeypatch.setattr("otto_core.ia_local_runtime.IA_LOCAL_BASE_URL", "http://127.0.0.1:59999")
    monkeypatch.setattr("otto_core.ia_analise_store.IA_LOCAL_MODEL", "qwen2.5:3b")

    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    assert "012_ia_local_analise" in {
        r[0] for r in conn.execute("SELECT id FROM schema_migrations").fetchall()
    }
    _seed(conn)

    d1 = adicionar_documento(
        conn, "IA-1", "edital.txt", b"Edital exige certidao federal negativa.", "text/plain"
    )
    update_campo(
        conn,
        "IA-1",
        "objeto",
        AnaliseCampoUpdate(valor="Valor confirmado pelo usuario", natureza="usuario"),
    )

    st = status_runtime(base_url="http://127.0.0.1:59999")
    assert st["disponivel"] is False
    assert st["nuvem"] is False

    job = iniciar_analise(conn, "IA-1", [d1.id], db_path=str(db))
    assert job["status"] == "falhou"
    assert "indispon" in (job["erro"] + job["progresso"]).lower() or "ollama" in job["erro"].lower()

    # Inserir sugestão artificial e tentar aplicar sobre campo usuario sem forçar
    agora = "2026-11-04T00:00:00+00:00"
    cur = conn.execute(
        """
        INSERT INTO analise_ia_sugestoes (
          job_id, numero_controle_pncp, tipo, chave, titulo, valor,
          documento_id, pagina, trecho, referencia_confirmada, aviso_referencia,
          estado, criado_em
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            job["id"],
            "IA-1",
            "campo",
            "objeto",
            "Objeto",
            "Sugestao IA que nao deve sobrescrever",
            d1.id,
            None,
            "certidao federal negativa",
            1,
            "",
            "pendente",
            agora,
        ),
    )
    conn.commit()
    sug_id = int(cur.lastrowid)
    try:
        aplicar_sugestao(conn, "IA-1", sug_id, forcar_sobrescrita_usuario=False)
        assert False, "deveria bloquear sobrescrita"
    except ValueError as e:
        assert "usuário" in str(e).lower() or "usuario" in str(e).lower() or "preservado" in str(e).lower()

    # Mesmo com forcar=True: não amplia sobrescrita (fora do README)
    try:
        aplicar_sugestao(conn, "IA-1", sug_id, forcar_sobrescrita_usuario=True)
        assert False, "forcar=True também deve preservar origem usuário"
    except ValueError as e:
        assert "preservado" in str(e).lower() or "usuário" in str(e).lower() or "usuario" in str(e).lower()

    ficha = get_ficha(conn, "IA-1")
    obj = next(c for c in ficha.campos if c.chave == "objeto")
    assert obj.valor == "Valor confirmado pelo usuario"
    assert obj.natureza == "usuario"

    rejeitar_sugestao(conn, "IA-1", sug_id)
    pend = listar_sugestoes(conn, "IA-1", apenas_pendentes=True)
    assert all(s["id"] != sug_id for s in pend)
    conn.close()


def test_avaliar_referencia_txt_sem_pagina_ok():
    pags = [{"pagina": 1, "texto": "Quantidade: 200 cadeiras ergonômicas com garantia."}]
    ok, aviso, pag = avaliar_referencia_sugestao(
        trecho="200 cadeiras ergonômicas",
        pagina=None,
        paginas=pags,
        tipo_mime="text/plain",
        tipo_sugestao="campo",
    )
    assert ok is True
    assert aviso == ""
    # TXT: página pode ficar vazia; se localizável em 1 página, pode preencher.
    assert pag in (None, 1)


def test_avaliar_referencia_pdf_exige_pagina_ou_localiza():
    pags = [
        {"pagina": 1, "texto": "Objeto: fornecimento de cadeiras."},
        {"pagina": 2, "texto": "Valor estimado: R$ 180.000,00."},
        {"pagina": 3, "texto": "Prazo de entrega: 60 dias."},
    ]
    ok, aviso, pag = avaliar_referencia_sugestao(
        trecho="Valor estimado: R$ 180.000,00",
        pagina=None,
        paginas=pags,
        tipo_mime="application/pdf",
        tipo_sugestao="campo",
    )
    assert ok is True
    assert pag == 2

    ok2, aviso2, _ = avaliar_referencia_sugestao(
        trecho="",
        pagina=2,
        paginas=pags,
        tipo_mime="application/pdf",
        tipo_sugestao="campo",
    )
    assert ok2 is False
    assert "vazio" in aviso2.lower()


def test_avaliar_nao_inventa_trecho_ausente():
    pags = [{"pagina": 1, "texto": "Somente texto real do edital."}]
    ok, aviso, _ = avaliar_referencia_sugestao(
        trecho="visita técnica obrigatória inventada",
        pagina=1,
        paginas=pags,
        tipo_mime="application/pdf",
        tipo_sugestao="campo",
    )
    assert ok is False
    assert "não encontrado" in aviso.lower() or "nao encontrado" in aviso.lower()


def test_localizar_citacao_literal_sem_inventar():
    pags = [
        {"pagina": 1, "texto": "Objeto genérico."},
        {"pagina": 2, "texto": "Quantidade: 200 unidades. Valor estimado total: R$ 180.000,00."},
    ]
    cit, pag = localizar_citacao_no_documento("200 unidades.", pags)
    assert "200 unidades" in cit.casefold()
    assert pag == 2
    cit2, pag2 = localizar_citacao_no_documento("visita tecnica obrigatoria inventada xyz", pags)
    assert cit2 == ""
    assert pag2 is None


def test_cobertura_parcial_quando_parte_falha(tmp_path: Path, monkeypatch):
    """Falha em uma parte → status parcial; não declara cobertura completa."""
    db = tmp_path / "parcial.db"
    docs = tmp_path / "documentos"
    monkeypatch.setattr("otto_core.config.DATA_DIR", tmp_path)
    monkeypatch.setattr("otto_core.config.DB_PATH", db)
    monkeypatch.setattr("otto_core.document_store.DOCUMENTOS_DIR", docs)
    docs.mkdir()

    # Duas páginas → dois chunks (1 página por chunk com limite baixo)
    monkeypatch.setattr("otto_core.ia_analise_store.MAX_CHARS_CHUNK", 80)
    calls = {"n": 0}

    def fake_gerar(*, system: str, user: str, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            return {
                "campos": [
                    {
                        "chave": "objeto",
                        "valor": "Parte um do edital teste",
                        "pagina": 1,
                        "trecho": "Parte um do edital",
                    }
                ],
                "requisitos": [],
                "checklist": [],
            }
        raise IaLocalErro("falha simulada na parte 2")

    monkeypatch.setattr("otto_core.ia_analise_store.gerar_json_local", fake_gerar)
    monkeypatch.setattr(
        "otto_core.ia_analise_store.status_runtime",
        lambda: {
            "disponivel": True,
            "modelo_configurado": "qwen2.5:3b",
            "aviso": "",
            "nuvem": False,
        },
    )

    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    _seed(conn, "IA-PARCIAL")
    d1 = adicionar_documento(
        conn,
        "IA-PARCIAL",
        "parcial.txt",
        b"Parte um do edital teste com texto suficiente para citacao.",
        "text/plain",
    )
    # Segunda página artificial (TXT normal só gera 1)
    conn.execute(
        "INSERT INTO documento_paginas (documento_id, pagina, texto) VALUES (?,?,?)",
        (d1.id, 2, "Parte dois do edital teste com mais texto na pagina dois."),
    )
    conn.commit()

    import time

    from otto_core.ia_analise_store import get_job

    job = iniciar_analise(conn, "IA-PARCIAL", [d1.id], db_path=str(db))
    deadline = time.time() + 20
    final = None
    while time.time() < deadline:
        final = get_job(conn, "IA-PARCIAL", job["id"])
        if final and final["status"] in {"parcial", "concluido", "falhou"}:
            break
        time.sleep(0.2)
    assert final is not None
    assert final["status"] == "parcial"
    assert "1/2" in final["cobertura"]
    assert "Falha na parte" in final["cobertura"]
    assert "Processados:" in final["cobertura"]
    sug = listar_sugestoes(conn, "IA-PARCIAL", job_id=job["id"])
    assert any(s["chave"] == "objeto" for s in sug)
    conn.close()


def test_bloquear_aplicar_sem_evidencia_e_aplicar_com_evidencia(tmp_path: Path, monkeypatch):
    db = tmp_path / "ia2.db"
    docs = tmp_path / "documentos"
    monkeypatch.setattr("otto_core.config.DATA_DIR", tmp_path)
    monkeypatch.setattr("otto_core.config.DB_PATH", db)
    monkeypatch.setattr("otto_core.document_store.DOCUMENTOS_DIR", docs)
    docs.mkdir()
    monkeypatch.setattr("otto_core.ia_local_runtime.IA_LOCAL_BASE_URL", "http://127.0.0.1:59999")

    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    _seed(conn, "IA-2")
    d1 = adicionar_documento(
        conn,
        "IA-2",
        "edital.txt",
        b"Objeto: cadeiras. Quantidade: 200 unidades. Valor estimado 180000.",
        "text/plain",
    )
    job = iniciar_analise(conn, "IA-2", [d1.id], db_path=str(db))
    agora = "2026-11-05T00:00:00+00:00"

    cur_bad = conn.execute(
        """
        INSERT INTO analise_ia_sugestoes (
          job_id, numero_controle_pncp, tipo, chave, titulo, valor,
          documento_id, pagina, trecho, referencia_confirmada, aviso_referencia,
          estado, criado_em
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            job["id"],
            "IA-2",
            "campo",
            "quantidades",
            "Quantidades",
            "200",
            d1.id,
            None,
            "",
            0,
            "Trecho vazio — referência não confirmada.",
            "pendente",
            agora,
        ),
    )
    conn.commit()
    bad_id = int(cur_bad.lastrowid)
    try:
        aplicar_sugestao(conn, "IA-2", bad_id)
        assert False, "deveria bloquear apply sem evidência"
    except ValueError as e:
        assert "evidência" in str(e).lower() or "evidencia" in str(e).lower()

    ficha = get_ficha(conn, "IA-2")
    q = next(c for c in ficha.campos if c.chave == "quantidades")
    assert (q.valor or "") != "200" or q.natureza != "sugerido_ia"

    cur_ok = conn.execute(
        """
        INSERT INTO analise_ia_sugestoes (
          job_id, numero_controle_pncp, tipo, chave, titulo, valor,
          documento_id, pagina, trecho, referencia_confirmada, aviso_referencia,
          estado, criado_em
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            job["id"],
            "IA-2",
            "campo",
            "quantidades",
            "Quantidades",
            "200",
            d1.id,
            None,
            "Quantidade: 200 unidades",
            1,
            "",
            "pendente",
            agora,
        ),
    )
    conn.commit()
    ok_id = int(cur_ok.lastrowid)
    res = aplicar_sugestao(conn, "IA-2", ok_id)
    assert res["aplicado"] is True
    ficha2 = get_ficha(conn, "IA-2")
    q2 = next(c for c in ficha2.campos if c.chave == "quantidades")
    assert q2.valor == "200"
    assert q2.natureza == "sugerido_ia"
    conn.close()
