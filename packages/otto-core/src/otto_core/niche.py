"""
Classificador multi-nicho — regras locais (objeto + órgão).

DECISÃO (2026-11-06): setores além de TI para radar Brasil/UF; TI v2.2
preservado como `ti_software`. Ordem: setores específicos → TI → outros.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Literal

Confianca = Literal["alta", "baixa", "nenhuma"]

# IDs canônicos (filtro UI / coluna oportunidades.nicho)
NICHO_PASSAGENS = "passagens_viagens"
NICHO_SAUDE = "saude_medicamentos"
NICHO_OBRAS = "obras_engenharia"
NICHO_ALIMENTOS = "alimentos_merenda"
NICHO_ESCRITORIO = "material_escritorio_papelaria"
NICHO_LIMPEZA = "limpeza_conservacao"
NICHO_VEICULOS = "veiculos_combustiveis"
NICHO_TI = "ti_software"
NICHO_OUTROS = "outros"

NICHOS_ORDEM: list[str] = [
    NICHO_PASSAGENS,
    NICHO_SAUDE,
    NICHO_OBRAS,
    NICHO_ALIMENTOS,
    NICHO_ESCRITORIO,
    NICHO_LIMPEZA,
    NICHO_VEICULOS,
    NICHO_TI,
    NICHO_OUTROS,
]

NICHOS_LABELS: dict[str, str] = {
    NICHO_PASSAGENS: "Passagens / viagens",
    NICHO_SAUDE: "Saúde / medicamentos",
    NICHO_OBRAS: "Obras / engenharia",
    NICHO_ALIMENTOS: "Alimentos / merenda",
    NICHO_ESCRITORIO: "Material de escritório",
    NICHO_LIMPEZA: "Limpeza / conservação",
    NICHO_VEICULOS: "Veículos / combustíveis",
    NICHO_TI: "TI / software",
    NICHO_OUTROS: "Outros",
}

# --- setores (exceto TI) · frases e termos ---
_SETOR_RULES: list[tuple[str, list[str], list[str]]] = [
    (
        NICHO_PASSAGENS,
        [
            "passagem aerea",
            "passagens aereas",
            "agenciamento de viagens",
            "agencia de viagens",
            "bilhete aereo",
            "passagem rodoviaria",
        ],
        [
            "passagem aerea",
            "passagens",
            "agenciamento",
            "trecho aereo",
            "aereo nacional",
            "deslocamento aereo",
        ],
    ),
    (
        NICHO_SAUDE,
        [
            "material medico hospitalar",
            "material hospitalar",
            "dispositivo medico",
            "dispositivos medicos",
            "registro de precos para aquisicao de dispositivos medicos",
        ],
        [
            "medicamento",
            "medicamentos",
            "hospitalar",
            "opme",
            "laboratorio",
            "laboratorial",
            "fisioterapia",
            "odontologico",
            "farmacia",
            "insumo hospitalar",
            "vacina",
            "seringas",
            "reativo",
            "diagnostico por imagem",
            "material medico",
        ],
    ),
    (
        NICHO_OBRAS,
        [
            "engenharia civil",
            "construcao civil",
            "material de construcao",
        ],
        [
            "obra",
            "obras",
            "pavimentacao",
            "reforma",
            "terraplenagem",
            "construcao",
            "edificacao",
            "alvenaria",
            "drenagem",
            "recuperacao asfaltica",
            "calcamento",
            "engenharia",
        ],
    ),
    (
        NICHO_ALIMENTOS,
        [
            "merenda escolar",
            "cesta basica",
            "cestas basicas",
            "genero alimenticio",
            "generos alimenticios",
        ],
        [
            "merenda",
            "alimentacao",
            "alimento",
            "alimentos",
            "cozinheiro",
            "cozinha",
            "hortifruti",
            "generos alimenticios",
            "lanche",
            "refeicao",
        ],
    ),
    (
        NICHO_ESCRITORIO,
        [
            "material de expediente",
            "material de escritorio",
            "artigos de papelaria",
        ],
        [
            "escritorio",
            "papelaria",
            "expediente",
            "sulfite",
            "toner",
            "cartucho",
            "resma",
            "grampeador",
        ],
    ),
    (
        NICHO_LIMPEZA,
        [
            "material de limpeza",
            "servicos de limpeza",
            "limpeza e conservacao",
        ],
        [
            "limpeza",
            "conservacao",
            "higienizacao",
            "detergente",
            "desinfetante",
            "jardinagem",
            "coleta de residuos",
        ],
    ),
    (
        NICHO_VEICULOS,
        [
            "locacao de caminhao",
            "transporte escolar",
        ],
        [
            "veiculo",
            "veiculos",
            "combustivel",
            "combustiveis",
            "frota",
            "automotor",
            "caminhao",
            "onibus",
            "gasolina",
            "diesel",
            "etanol",
            "pneus",
            "pecas automotivas",
        ],
    ),
]

# --- TI v2.2 (preservado) ---
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
    "servidores",
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

WEAK_TERMS = [
    "sistema",
    "sistemas",
    "digital",
    "eletronico",
    "manutencao",
    "servico tecnico",
    "implementacao",
    "api",
    "app",
]

# Bloqueios que ainda anulam TI (não cobertos como setor próprio, ou ambíguos)
BLOCK_PHRASES = [
    "portal de compras publicas",
    "pregao eletronico",
    "hospedagem com cafe da manha",
    "evento presencial",
    "iluminacao publica",
    "assistencia social",
    "sistema unico de assistencia",
    "beneficios eventuais",
]

BLOCK_TERMS = [
    "mobiliario",
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
_SERVIDOR_HUMANO_RE = re.compile(
    r"\bservidores?\b.{0,48}\b("
    r"municipal|municipais|publico|publicos|publica|publicas|"
    r"estatutari\w*|comissionad\w*|da prefeitura|do municipio|"
    r"federais|estaduais|civis"
    r")\b"
    r"|"
    r"\b("
    r"municipal|municipais|publico|publicos|"
    r"da prefeitura|do municipio"
    r")\b.{0,48}\bservidores?\b",
)


def _ascii_lower(text: str) -> str:
    folded = unicodedata.normalize("NFKD", text)
    return folded.encode("ascii", "ignore").decode("ascii").lower()


def _fold(text: str) -> str:
    return f" {_ascii_lower(text)} "


def _term_pattern(term_folded: str) -> re.Pattern[str]:
    parts = [re.escape(p) for p in term_folded.split() if p]
    if not parts:
        return re.compile(r"(?!x)x")
    body = r"\s+".join(parts)
    return re.compile(rf"(?<![a-z0-9]){body}(?![a-z0-9])")


def _match_phrases(text: str, phrases: list[str]) -> list[str]:
    found: list[str] = []
    for phrase in phrases:
        p = _ascii_lower(phrase)
        if p and p in text:
            found.append(phrase)
    return found


def _match_terms(text: str, terms: list[str]) -> list[str]:
    found: list[str] = []
    for term in terms:
        t = _ascii_lower(term)
        if not t:
            continue
        if _term_pattern(t).search(text):
            found.append(term)
    return found


def _hospedagem_ti_context(text: str, hosting_phrases: list[str]) -> bool:
    if hosting_phrases:
        return True
    if not _HOSPEDAGEM_RE.search(text):
        return False
    return any(ctx in text for ctx in _HOSPEDAGEM_TI_CONTEXT)


def _strip_servidor_humano(text: str, strong: list[str]) -> list[str]:
    if not _SERVIDOR_HUMANO_RE.search(text):
        return strong
    return [s for s in strong if _ascii_lower(s) not in {"servidor", "servidores"}]


def _classify_setor(text: str) -> tuple[str, Confianca, list[str]] | None:
    for nicho, phrases, terms in _SETOR_RULES:
        ph = _match_phrases(text, phrases)
        tm = _match_terms(text, terms)
        hits = ph + tm
        if not hits:
            continue
        conf: Confianca = "alta" if ph or len(tm) >= 2 else "baixa"
        return nicho, conf, hits
    return None


def _classify_ti(text: str) -> tuple[str, Confianca, list[str]]:
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

    if _HOSPEDAGEM_RE.search(text) and not _hospedagem_ti_context(text, hosting_phrase_hits):
        strong = [s for s in strong if "hospedagem" not in s.lower()]

    strong = _strip_servidor_humano(text, strong)

    weak = _match_terms(text, WEAK_TERMS)
    strong_set = {_ascii_lower(s) for s in strong}
    weak = [w for w in weak if _ascii_lower(w) not in strong_set]

    if blocks:
        return NICHO_OUTROS, "nenhuma", blocks

    signals = strong + weak
    if strong:
        return NICHO_TI, "alta", signals
    if len(weak) >= 2:
        return NICHO_TI, "baixa", signals

    return NICHO_OUTROS, "nenhuma", []


def classify_nicho(
    objeto: str,
    orgao: str = "",
) -> tuple[str, Confianca, list[str]]:
    """
    Classifica nicho por regras locais sobre objeto (+ órgão opcional).
    Setores específicos têm prioridade sobre TI; residual → outros.
    """
    text = _fold(f"{objeto or ''} {orgao or ''}")
    setor = _classify_setor(text)
    if setor is not None:
        return setor
    return _classify_ti(text)
