"""§14 — especializações Saúde / Viagens (só sinais do objeto)."""
from __future__ import annotations

from otto_core.especializacao import classificar_especializacao
from otto_core.niche import NICHO_PASSAGENS, NICHO_SAUDE, NICHO_TI


def test_saude_medicamentos_e_materiais():
    r = classificar_especializacao(
        "Aquisição de medicamentos e material médico hospitalar com entrega",
        NICHO_SAUDE,
    )
    assert r["especializacao"] == "saude"
    ids = {s["id"] for s in r["subtipos"]}
    assert "medicamentos" in ids
    assert "materiais" in ids
    assert any(c["id"] == "entrega_execucao" for c in r["condicoes_mencionadas"])
    assert any("não inferir" in x.lower() or "nao inferir" in x.lower() for x in r["limitacoes"])


def test_saude_equipamentos_servicos():
    r = classificar_especializacao(
        "Contratação de exames de Holter e serviços médico-veterinários",
        NICHO_SAUDE,
    )
    ids = {s["id"] for s in r["subtipos"]}
    assert "equipamentos" in ids or "servicos" in ids


def test_viagens_agenciamento_passagens_condicoes():
    r = classificar_especializacao(
        "Agenciamento de viagens com passagem aérea, emissão, alteração e cancelamento",
        NICHO_PASSAGENS,
    )
    assert r["especializacao"] == "viagens"
    ids = {s["id"] for s in r["subtipos"]}
    assert "agenciamento" in ids
    assert "passagens" in ids
    cids = {c["id"] for c in r["condicoes_mencionadas"]}
    assert "emissao" in cids
    assert "alteracao" in cids
    assert "cancelamento" in cids


def test_sem_especializacao_fora_saude_viagens():
    r = classificar_especializacao("Contratação de software ERP", NICHO_TI)
    assert r["especializacao"] is None
    assert r["subtipos"] == []


def test_nao_inventa_subtipo_sem_sinal():
    r = classificar_especializacao(
        "Aquisição de itens diversos para a secretaria de saúde do município",
        NICHO_SAUDE,
    )
    assert r["especializacao"] == "saude"
    # Sem termo de medicamento/material/etc. no objeto → sem subtipo inventado
    assert r["subtipos"] == []
    assert r["condicoes_mencionadas"] == []
