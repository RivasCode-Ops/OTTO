from __future__ import annotations

import pytest

from otto_core.niche import classify_nicho
from otto_core.normalize import extract_numero_controle, normalize_pncp_item
from otto_core.score import compute_score
from otto_core.models import Oportunidade

# --- amostras reais PI (falsos positivos corrigidos) ---

MOBILIARIO_UNIAO = (
    "[Portal de Compras Públicas] - CONTRATAÇÃO DE EMPRESA PARA AQUISIÇÃO DE "
    "MATERIAL PERMANENTE - MOBILIÁRIO, PARA ATENDER ÀS NECESSIDADES DA SECRETARIA "
    "MUNICIPAL DE SAÚDE DE UNIÃO-PI."
)

MEDICAMENTOS_GUADALUPE = (
    "Registro de Preço, para FORNECIMENTO DE MATERIAL PERMANENTE E DE CONSUMO "
    "(MEDICAMENTOS, MATERIAL MÉDICO HOSPITALAR, FISIOTERAPIA, LABORATÓRIO E "
    "ODONTOLÓGICO) PARA SUPRIR AS NECESSIDADES DA SECRETARIA MUNICIPAL DE SAÚDE"
)

PGE_INFRA_TI = (
    "Aquisição de Infraestrutura de Tecnologia da Informação - TI, incluindo "
    "microcomputadores, equipamentos com foco em ambientes de virtualização, "
    "backup, armazenamento de dados em larga escala"
)

COZINHEIRO_IFPI = (
    "Contratação de empresa especializada para prestação de serviços de "
    "COZINHEIRO e AUXILIAR DE COZINHA mediante sistema de registro de preços"
)


def test_classify_ti_alta_strong_terms():
    nicho, conf, matches = classify_nicho("Contratação de software ERP e licença de sistemas")
    assert nicho == "ti_software"
    assert conf == "alta"
    assert "software" in matches or "erp" in matches


def test_classify_ti_alta_pge_real():
    nicho, conf, _ = classify_nicho(PGE_INFRA_TI)
    assert nicho == "ti_software"
    assert conf == "alta"


def test_classify_outros_escritorio():
    nicho, conf, _ = classify_nicho("Aquisição de material de escritório")
    assert nicho == "outros"
    assert conf == "nenhuma"


def test_block_portal_compras_mobiliario():
    nicho, conf, matches = classify_nicho(MOBILIARIO_UNIAO)
    assert nicho == "outros"
    assert conf == "nenhuma"
    assert any("portal" in m.lower() or "mobili" in m.lower() for m in matches)


def test_block_medicamentos():
    nicho, conf, _ = classify_nicho(MEDICAMENTOS_GUADALUPE)
    assert nicho == "outros"
    assert conf == "nenhuma"


def test_block_cozinheiro():
    nicho, conf, _ = classify_nicho(COZINHEIRO_IFPI)
    assert nicho == "outros"
    assert conf == "nenhuma"


def test_weak_only_sistema_outros():
    nicho, conf, _ = classify_nicho("Contratação de sistema genérico administrativo")
    assert nicho == "outros"
    assert conf == "nenhuma"


def test_block_hospedagem_hotelaria():
    nicho, conf, _ = classify_nicho(
        "registro de preços para contratação dos serviços de hospedagem/hotelaria"
    )
    assert nicho == "outros"
    assert conf == "nenhuma"


def test_hospedagem_sistemas_alta():
    nicho, conf, matches = classify_nicho(
        "Contratação de hospedagem de sistemas em nuvem para portal institucional"
    )
    assert nicho == "ti_software"
    assert conf == "alta"
    assert any("hospedagem" in m or "nuvem" in m for m in matches)


def test_hosting_cloud_alta():
    nicho, conf, _ = classify_nicho("Serviço de hosting e cloud para aplicações críticas")
    assert nicho == "ti_software"
    assert conf == "alta"


def test_two_weak_baixa():
    nicho, conf, _ = classify_nicho("Serviço digital com sistema eletrônico")
    assert nicho == "ti_software"
    assert conf == "baixa"


def test_normalize_minimal():
    raw = {
        "numeroControlePNCP": "12345-1-000001/2026",
        "sequencialCompra": 1,
        "objetoCompra": "Sistema de gestão",
        "orgaoEntidade": {"razaoSocial": "Prefeitura Teste"},
        "unidadeOrgao": {"ufSigla": "SP"},
        "valorTotalEstimado": 250000,
        "situacaoCompraNome": "Publicada",
    }
    data = normalize_pncp_item(raw)
    assert data["uf"] == "SP"
    assert data["valor_total_estimado"] == 250000
    assert extract_numero_controle(raw) == "12345-1-000001/2026"


def test_score_range():
    opp = Oportunidade(
        numero_controle_pncp="x",
        objeto_compra="software",
        nicho="ti_software",
        confianca_classificacao="alta",
        valor_total_estimado=500000,
    )
    scored = compute_score(opp, orgao_historico=2)
    assert 0 <= scored.score_total <= 100
    assert scored.score_detalhe.valor >= 0
