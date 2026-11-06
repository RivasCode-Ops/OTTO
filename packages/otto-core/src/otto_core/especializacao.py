"""Especializações setoriais Saúde e Viagens (README §14).

DECISÃO (2026-11-06): extensão determinística sobre o *objeto* já classificado
como `saude_medicamentos` ou `passagens_viagens`. Subtipos e condições só
quando há sinal textual no objeto — não inventar exigências pela categoria.
Regras locais, revisáveis (listas abaixo). Sem integração LX Saúde / app de
viagens (independência §15.1).
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any, Literal

from otto_core.niche import NICHO_PASSAGENS, NICHO_SAUDE, NICHOS_LABELS

EspecializacaoId = Literal["saude", "viagens"]

# --- Saúde: subtipos (README §14) ---
_SAUDE_SUBTIPOS: list[tuple[str, str, list[str]]] = [
    (
        "medicamentos",
        "Medicamentos",
        ["medicamento", "medicamentos", "farmacia", "farmacêutico", "farmaceutico", "vacina", "vacinas", "insumo farmaceutico"],
    ),
    (
        "materiais",
        "Materiais",
        [
            "material medico",
            "material hospitalar",
            "materiais medicos",
            "opme",
            "seringas",
            "reativo",
            "insumo hospitalar",
            "dispositivo medico",
            "dispositivos medicos",
        ],
    ),
    (
        "equipamentos",
        "Equipamentos",
        [
            "equipamento medico",
            "equipamentos medicos",
            "aparelho",
            "aparelhos",
            "diagnostico por imagem",
            "monitorizacao",
            "holter",
            "mapa 24",
            "respirador",
            "autoclave",
        ],
    ),
    (
        "servicos",
        "Serviços",
        [
            "servico medico",
            "servicos medicos",
            "servico hospitalar",
            "fisioterapia",
            "exame",
            "exames",
            "consulta medica",
            "atendimento ambulatorial",
            "medico veterinario",
            "medico-veterinario",
        ],
    ),
]

_SAUDE_CONDICOES: list[tuple[str, str, list[str]]] = [
    (
        "entrega_execucao",
        "Condições de entrega/execução mencionadas no objeto",
        ["entrega", "fornecido", "fornecimento", "execucao", "execução", "instalacao", "instalação"],
    ),
    (
        "requisito_tecnico",
        "Requisito técnico mencionado no objeto",
        ["especificacao tecnica", "especificação técnica", "termo de referencia", "termo de referência", "anvisa", "cnes"],
    ),
]

# --- Viagens ---
_VIAGENS_SUBTIPOS: list[tuple[str, str, list[str]]] = [
    (
        "passagens",
        "Passagens",
        ["passagem", "passagens", "bilhete aereo", "bilhete aéreo", "trecho aereo", "aereo nacional"],
    ),
    (
        "hospedagem",
        "Hospedagem",
        ["hospedagem", "hotel", "hoteis", "hotéis", "diaria", "diária", "pousada"],
    ),
    (
        "agenciamento",
        "Agenciamento",
        ["agenciamento", "agencia de viagens", "agência de viagens", "operadora de turismo"],
    ),
    (
        "atendimento",
        "Atendimento",
        ["atendimento", "suporte ao passageiro", "assistencia ao viajante", "assistência ao viajante"],
    ),
]

_VIAGENS_CONDICOES: list[tuple[str, str, list[str]]] = [
    (
        "emissao",
        "Emissão mencionada no objeto",
        ["emissao", "emissão", "emitir bilhete", "emissao de bilhete"],
    ),
    (
        "alteracao",
        "Alteração mencionada no objeto",
        ["alteracao", "alteração", "remarcar", "remarcacao", "remarcação"],
    ),
    (
        "cancelamento",
        "Cancelamento mencionado no objeto",
        ["cancelamento", "cancelar", "reembolso"],
    ),
]


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", s.lower()).strip()


def _hits(texto: str, termos: list[str]) -> list[str]:
    found: list[str] = []
    for t in termos:
        tn = _norm(t)
        if not tn:
            continue
        # frase: substring; termo curto: fronteira aproximada
        if " " in tn:
            if tn in texto:
                found.append(t)
        else:
            if re.search(rf"(?<!\w){re.escape(tn)}(?!\w)", texto):
                found.append(t)
    return found


def classificar_especializacao(
    objeto: str,
    nicho: str | None,
    *,
    orgao: str = "",
) -> dict[str, Any]:
    """Retorna especialização §14 ou null se o nicho não for Saúde/Viagens."""
    n = (nicho or "").strip()
    texto = _norm(f"{objeto or ''} {orgao or ''}")

    if n == NICHO_SAUDE:
        return _montar("saude", "Saúde", texto, _SAUDE_SUBTIPOS, _SAUDE_CONDICOES, n)
    if n == NICHO_PASSAGENS:
        return _montar("viagens", "Viagens", texto, _VIAGENS_SUBTIPOS, _VIAGENS_CONDICOES, n)

    return {
        "especializacao": None,
        "rotulo": None,
        "nicho": n or None,
        "nicho_rotulo": NICHOS_LABELS.get(n) if n else None,
        "subtipos": [],
        "condicoes_mencionadas": [],
        "aviso": (
            "Especialização Saúde/Viagens só se aplica quando o nicho da oportunidade "
            "é Saúde / medicamentos ou Passagens / viagens."
        ),
        "limitacoes": [
            "Não inferir exigências só pela categoria/nicho.",
            "Sinais vêm apenas do texto do objeto (e órgão, se informado).",
            "Documentos anexos não são lidos nesta etapa.",
        ],
    }


def _montar(
    esp_id: EspecializacaoId,
    rotulo: str,
    texto: str,
    subtipos_rules: list[tuple[str, str, list[str]]],
    condicoes_rules: list[tuple[str, str, list[str]]],
    nicho: str,
) -> dict[str, Any]:
    subtipos: list[dict[str, Any]] = []
    for sid, srot, termos in subtipos_rules:
        h = _hits(texto, termos)
        if h:
            subtipos.append(
                {
                    "id": sid,
                    "rotulo": srot,
                    "sinais": h,
                    "fonte": "objeto",
                }
            )

    condicoes: list[dict[str, Any]] = []
    for cid, crot, termos in condicoes_rules:
        h = _hits(texto, termos)
        if h:
            condicoes.append(
                {
                    "id": cid,
                    "rotulo": crot,
                    "sinais": h,
                    "fonte": "objeto",
                }
            )

    return {
        "especializacao": esp_id,
        "rotulo": rotulo,
        "nicho": nicho,
        "nicho_rotulo": NICHOS_LABELS.get(nicho, nicho),
        "subtipos": subtipos,
        "condicoes_mencionadas": condicoes,
        "aviso": (
            f"Especialização {rotulo}: subtipos e condições listados só quando "
            "aparecem no objeto. Ausência de sinal ≠ ausência de exigência no edital."
        ),
        "limitacoes": [
            "Não inferir todas as exigências apenas pela categoria.",
            "Regras locais revisáveis em otto_core.especializacao.",
            "Sem leitura de PDF/DOCX nesta etapa; sem LX Saúde / app de viagens.",
            "Sem dados suficientes no objeto, a lista de subtipos pode ficar vazia.",
        ],
    }
