from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from otto_core.analise_store import (
    checklist_from_campo,
    confirmar_revisao_ficha,
    get_ficha,
    update_campo,
)
from otto_core.backup import criar_backup, restaurar_em_copia
from otto_core.db import init_db
from otto_core.document_store import adicionar_documento
from otto_core.financeiro_store import list_cenarios, upsert_cenario
from otto_core.fluxo_store import get_fluxo, update_fluxo
from otto_core.models import (
    AnaliseCampoUpdate,
    CenarioFinanceiroUpsert,
    FluxoUpdate,
)


def _seed(conn: sqlite3.Connection, numero: str = "PNCP-L4/1") -> None:
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
            "Orgao",
            "PI",
            "Objeto L4",
            "Publicada",
            "2026-01-10T12:00:00",
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


def _conn(tmp_path: Path, monkeypatch):
    db = tmp_path / "c.db"
    docs = tmp_path / "documentos"
    docs.mkdir()
    monkeypatch.setattr("otto_core.config.DATA_DIR", tmp_path)
    monkeypatch.setattr("otto_core.config.DB_PATH", db)
    monkeypatch.setattr("otto_core.document_store.DOCUMENTOS_DIR", docs)
    monkeypatch.setattr("otto_core.backup.DATA_DIR", tmp_path)
    monkeypatch.setattr("otto_core.backup.DB_PATH", db)
    monkeypatch.setattr("otto_core.backup.DOCUMENTOS_DIR", docs)
    monkeypatch.setattr("otto_core.backup.BACKUPS_DIR", tmp_path / "backups")
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    _seed(conn)
    return conn, db, docs


def test_rastreio_versao_fluxo_financeiro_backup(tmp_path: Path, monkeypatch):
    conn, db, docs = _conn(tmp_path, monkeypatch)

    update_campo(
        conn,
        "PNCP-L4/1",
        "itens_lotes",
        AnaliseCampoUpdate(valor="Lote A", natureza="usuario", trecho="manual"),
    )
    item = checklist_from_campo(conn, "PNCP-L4/1", "itens_lotes")
    assert item.requisito_chave == "itens_lotes"

    d1 = adicionar_documento(conn, "PNCP-L4/1", "edital.txt", b"v1 texto", "text/plain")
    update_campo(
        conn,
        "PNCP-L4/1",
        "docs_requisitos",
        AnaliseCampoUpdate(
            valor="Certidão",
            natureza="usuario",
            documento_id=d1.id,
            pagina=1,
            trecho="certidao",
        ),
    )
    d2 = adicionar_documento(conn, "PNCP-L4/1", "edital.txt", b"v2 texto novo", "text/plain")
    assert d2.versao == 2
    ficha = get_ficha(conn, "PNCP-L4/1")
    assert ficha.status == "desatualizada"
    assert any(c.precisa_revisao for c in ficha.campos if c.chave == "docs_requisitos")
    # valores preservados
    assert next(c for c in ficha.campos if c.chave == "docs_requisitos").valor == "Certidão"

    ficha = confirmar_revisao_ficha(conn, "PNCP-L4/1")
    assert ficha.status != "desatualizada" or not any(c.precisa_revisao for c in ficha.campos)

    fluxo = update_fluxo(
        conn,
        "PNCP-L4/1",
        FluxoUpdate(estado_fluxo="em_preparacao", resultado_disputa="pendente"),
    )
    assert fluxo.estado_fluxo == "em_preparacao"
    assert get_fluxo(conn, "PNCP-L4/1").resultado_contratacao == "nao_informado"

    c = upsert_cenario(
        conn,
        "PNCP-L4/1",
        CenarioFinanceiroUpsert(receita_estimada=1000, frete=50, premissas=""),
    )
    assert c.incompleto is True
    assert "lucro" not in " ".join(c.avisos).lower() or "não" in " ".join(c.avisos).lower()
    c2 = upsert_cenario(
        conn,
        "PNCP-L4/1",
        CenarioFinanceiroUpsert(
            receita_estimada=1000,
            frete=50,
            premissas="Preços de cotação X",
            escopo_parcial=True,
        ),
        cenario_id=c.id,
    )
    assert c2.custos_registrados == 50
    assert c2.saldo_sobre_custos_registrados == 950
    assert any("parcial" in a.lower() or "lucro" in a.lower() for a in c2.avisos)
    assert len(list_cenarios(conn, "PNCP-L4/1")) == 1

    c3 = upsert_cenario(
        conn,
        "PNCP-L4/1",
        CenarioFinanceiroUpsert(
            receita_estimada=1000,
            frete=50,
            premissas="Preços de cotação X",
            receita_realizada=900,
            custos_realizados=80,
        ),
        cenario_id=c2.id,
    )
    assert c3.saldo_realizado == 820
    assert c3.necessidade_caixa_estimada == 50
    assert any("realizado" in a.lower() for a in c3.avisos)
    assert any("difere" in a.lower() for a in c3.avisos)
    assert any("caixa" in a.lower() for a in c3.avisos)

    conn.close()
    info = criar_backup(tmp_path / "backups")
    zip_path = Path(info["arquivo"])
    assert zip_path.is_file()
    resto = restaurar_em_copia(zip_path, tmp_path / "restore-isolado")
    assert Path(resto["db"]).is_file()
    assert resto["oportunidades"] >= 1
    # operacional intacto
    assert db.is_file()
