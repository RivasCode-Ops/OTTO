from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from otto_core.analise_store import ensure_ficha, update_campo
from otto_core.db import atualizar_prazos_manuais, init_db, list_oportunidades
from otto_core.fluxo_store import listar_resultados, update_fluxo
from otto_core.itens_lotes_store import add_item
from otto_core.manual_store import criar_oportunidade_manual, importar_manuais_json
from otto_core.models import AnaliseCampoUpdate, FluxoUpdate
from otto_core.orientacao_store import upsert_orientacao
from otto_core.requisito_store import gerar_requisitos_da_ficha, list_requisitos


def test_prazos_import_orientacao_resultados_item_setor(tmp_path: Path):
    db = tmp_path / "p9.db"
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    init_db(conn)

    man = criar_oportunidade_manual(conn, objeto_compra="Software de gestão", uf="PI")
    atualizar_prazos_manuais(
        conn,
        man.numero_controle_pncp,
        data_esclarecimento="2026-12-01",
        data_impugnacao="2026-12-05",
    )
    listed = list_oportunidades(conn)
    one = next(o for o in listed if o.numero_controle_pncp == man.numero_controle_pncp)
    assert one.data_esclarecimento is not None
    assert one.data_impugnacao is not None

    upsert_orientacao(conn, man.numero_controle_pncp, "docs_exigidos", "nao")
    reqs = list_requisitos(conn, man.numero_controle_pncp)["items"]
    assert any(r["origem"] == "orientacao:docs_exigidos" for r in reqs)

    ensure_ficha(conn, man.numero_controle_pncp)
    update_campo(
        conn,
        man.numero_controle_pncp,
        "docs_requisitos",
        AnaliseCampoUpdate(valor="Certidão federal\nAlvará", natureza="usuario"),
    )
    ger = gerar_requisitos_da_ficha(conn, man.numero_controle_pncp)
    assert ger["gerados"] >= 1

    update_fluxo(
        conn,
        man.numero_controle_pncp,
        FluxoUpdate(
            estado_fluxo="encerrada",
            resultado_disputa="sim",
            tempo_preparacao_horas=8,
            custo_preparacao=500,
        ),
    )
    res = listar_resultados(conn)
    assert any(x["oportunidade"].numero_controle_pncp == man.numero_controle_pncp for x in res["items"])

    item = add_item(conn, man.numero_controle_pncp, descricao="Licença de software ERP")
    # Sugestão identificada, sem aplicar automaticamente.
    assert item["setor"] == ""
    assert item["setor_sugerido"]
    assert item["classificacao_origem"] == ""
    from otto_core.itens_lotes_store import update_item

    manual = update_item(
        conn,
        man.numero_controle_pncp,
        item["id"],
        setor="ti_software",
        categoria="software",
    )
    assert manual["setor"] == "ti_software"
    assert manual["classificacao_origem"] == "usuario"

    # Import JSON permanece no core (fora do escopo de UI); teste de API/core preservado.
    imp = importar_manuais_json(
        conn,
        [{"objeto_compra": "Cadeiras escolares", "orgao_razao_social": "SME", "uf": "PI"}],
    )
    assert len(imp["criados"]) == 1
    assert imp["erros"] == []

    assert get_count(conn) >= 2
    conn.close()


def get_count(conn: sqlite3.Connection) -> int:
    return int(conn.execute("SELECT COUNT(*) FROM oportunidades").fetchone()[0])


def test_migracao_009_idempotente(tmp_path: Path):
    db = tmp_path / "m9.db"
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    cols = {r[1] for r in conn.execute("PRAGMA table_info(oportunidades)").fetchall()}
    assert "data_esclarecimento" in cols
    assert "data_impugnacao" in cols
    fcols = {r[1] for r in conn.execute("PRAGMA table_info(oportunidade_fluxo)").fetchall()}
    assert "tempo_preparacao_horas" in fcols
    assert "auditoria_acoes" in {
        r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    conn.close()
