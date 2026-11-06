from __future__ import annotations

import re
import unicodedata
from typing import Literal

# --- v2.1 · termos fortes (frases primeiro) ---
STRONG_PHRASES = [
    "tecnologia da informacao",
    "infraestrutura de ti",
    "desenvolvimento de software",
    "sistema de gestao",
    "equipamento de informatica",
    "link de internet",
    "infraestrutura de rede",
    "equipamento de rede",
    "rede de dados",
    "suporte tecnico de ti",
    "hospedagem de sistemas",
    "hospedagem de sites",
    "hospedagem em nuvem",
    "hospedagem web",
]

STRONG_TERMS = [
    "software",
    "licenca",
    "licenciamento",
    "saas",
    "informatica",
    "computador",
    "notebook",
    "desktop",
    "servidor",
    "firewall",
    "switch",
    "roteador",
    "erp",
    "aplicativo",
    "impressora",
    "scanner",
    "datacenter",
    "data center",
    "banco de dados",
    "cybersecurity",
    "ciberseguranca",
    "inteligencia artificial",
    "machine learning",
    "virtualizacao",
    "backup",
    "hosting",
    "cloud",
    "nuvem",
    "dominio",
    "crm",
]

# Termos ambíguos — exigem 2+ combinados, sem bloqueio
WEAK_TERMS = [
    "sistema",
    "sistemas",
    "digital",
    "eletronico",
    "manutencao",
    "servico tecnico",
    "implementacao",
    "desenvolvimento",
    "api",
    "app",
]

# Bloqueios — anulam classificação TI
BLOCK_PHRASES = [
    "portal de compras publicas",
    "pregao eletronico",
    "hospedagem com cafe da manha",
    "evento presencial",
]

BLOCK_TERMS = [
    "medicamento",
    "hospitalar",
    "mobiliario",
    "merenda",
    "alimentacao",
    "cozinheiro",
    "material de limpeza",
    "combustivel",
    "engenharia civil",
    "construcao civil",
    "material de construcao",
    "cozinha",
    "fisioterapia",
    "odontologico",
    "caminhao",
    "locacao de caminhao",
    "veiculo",
    "automotor",
    "frota",
    "transporte escolar",
    "eletrodomestico",
    "rede publica",
    "hotelaria",
    "hotel",
    "pousada",
    "diaria",
    "apartamento",
    "cafe da manha",
    "almoco",
    "jantar",
]

# Contexto técnico válido para "hospedagem" (CATSER-style)
_HOSPEDAGEM_TI_CONTEXT = [
    "hosting",
    "cloud",
    "nuvem",
    "servidor",
    "datacenter",
    "data center",
    "dominio",
    "infraestrutura",
    "aplicacao",
    "aplicativo",
    "site web",
    "pagina web",
    "sistemas",
    "sistema",
]

_STRONG_WORD_RE = re.compile(r"\b(tic|ti)\b", re.IGNORECASE)
_HOSPEDAGEM_RE = re.compile(r"\bhospedagem\b")


def _fold(text: str) -> str:
    folded = unicodedata.normalize("NFKD", text)
    folded = folded.encode("ascii", "ignore").decode("ascii")
    return f" {folded.lower()} "


def _match_phrases(text: str, phrases: list[str]) -> list[str]:
    found: list[str] = []
    for phrase in phrases:
        p = unicodedata.normalize("NFKD", phrase).encode("ascii", "ignore").decode("ascii").lower()
        if p in text:
            found.append(phrase)
    return found


def _match_terms(text: str, terms: list[str]) -> list[str]:
    found: list[str] = []
    for term in terms:
        t = unicodedata.normalize("NFKD", term).encode("ascii", "ignore").decode("ascii").lower()
        if t in text:
            found.append(term)
    return found


def _hospedagem_ti_context(text: str, hosting_phrases: list[str]) -> bool:
    """Hospedagem só conta como TI com contexto técnico adjacente (v2.1)."""
    if hosting_phrases:
        return True
    if not _HOSPEDAGEM_RE.search(text):
        return False
    return any(ctx in text for ctx in _HOSPEDAGEM_TI_CONTEXT)


def classify_nicho(objeto: str) -> tuple[str, Literal["alta", "baixa", "nenhuma"], list[str]]:
    text = _fold(objeto)

    blocks = _match_phrases(text, BLOCK_PHRASES) + _match_terms(text, BLOCK_TERMS)

    hosting_phrases = [
        p
        for p in STRONG_PHRASES
        if p.startswith("hospedagem de") or p == "hospedagem web"
    ]
    hosting_phrase_hits = _match_phrases(text, hosting_phrases)

    strong = _match_phrases(text, STRONG_PHRASES) + _match_terms(text, STRONG_TERMS)
    if _STRONG_WORD_RE.search(text):
        strong.append("ti/tic")

    # hospedagem isolada (hotelaria) não é sinal TI
    if _HOSPEDAGEM_RE.search(text) and not _hospedagem_ti_context(text, hosting_phrase_hits):
        strong = [s for s in strong if "hospedagem" not in s.lower()]

    weak = _match_terms(text, WEAK_TERMS)
    strong_set = {
        unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower() for s in strong
    }
    weak = [
        w
        for w in weak
        if unicodedata.normalize("NFKD", w).encode("ascii", "ignore").decode().lower() not in strong_set
    ]

    if blocks:
        return "outros", "nenhuma", blocks

    signals = strong + weak
    if strong:
        return "ti_software", "alta", signals
    if len(weak) >= 2:
        return "ti_software", "baixa", signals

    return "outros", "nenhuma", []
