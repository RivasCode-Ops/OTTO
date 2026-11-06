"""Uma regra (amostra) por setor do classificador multi-nicho."""
from __future__ import annotations

from otto_core.niche import (
    NICHO_ALIMENTOS,
    NICHO_ESCRITORIO,
    NICHO_LIMPEZA,
    NICHO_OBRAS,
    NICHO_OUTROS,
    NICHO_PASSAGENS,
    NICHO_SAUDE,
    NICHO_TI,
    NICHO_VEICULOS,
    classify_nicho,
)


def test_saude_medicamentos():
    nicho, conf, hits = classify_nicho(
        "Registro de Preços para aquisição de medicamentos e material médico hospitalar"
    )
    assert nicho == NICHO_SAUDE
    assert conf in ("alta", "baixa")
    assert hits


def test_obras_engenharia():
    nicho, conf, _ = classify_nicho(
        "Contratação de empresa para pavimentação e terraplenagem de vias urbanas"
    )
    assert nicho == NICHO_OBRAS
    assert conf in ("alta", "baixa")


def test_passagens_viagens():
    nicho, conf, _ = classify_nicho(
        "Agenciamento de viagens e passagem aérea para servidores em deslocamento"
    )
    assert nicho == NICHO_PASSAGENS


def test_alimentos_merenda():
    nicho, conf, _ = classify_nicho(
        "Aquisição de gêneros alimentícios para merenda escolar municipal"
    )
    assert nicho == NICHO_ALIMENTOS


def test_material_escritorio():
    nicho, conf, _ = classify_nicho("Aquisição de material de escritório e papelaria")
    assert nicho == NICHO_ESCRITORIO


def test_limpeza_conservacao():
    nicho, conf, _ = classify_nicho(
        "Contratação de serviços de limpeza e conservação predial"
    )
    assert nicho == NICHO_LIMPEZA


def test_veiculos_combustiveis():
    nicho, conf, _ = classify_nicho(
        "Registro de preços para aquisição de combustíveis para a frota municipal"
    )
    assert nicho == NICHO_VEICULOS


def test_ti_preservado():
    nicho, conf, _ = classify_nicho("Contratação de software ERP e licença de sistemas")
    assert nicho == NICHO_TI
    assert conf == "alta"


def test_outros_residual():
    nicho, conf, _ = classify_nicho("Aquisição de bandeiras e flâmulas cerimoniais")
    assert nicho == NICHO_OUTROS
    assert conf == "nenhuma"


def test_orgao_ajuda_contexto():
    """Órgão entra no texto classificado (sem forçar setor só pelo nome genérico)."""
    nicho, _, _ = classify_nicho(
        "Fornecimento de medicamentos controlados",
        orgao="SECRETARIA MUNICIPAL DE SAUDE",
    )
    assert nicho == NICHO_SAUDE
