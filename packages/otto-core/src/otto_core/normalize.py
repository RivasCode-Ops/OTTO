from __future__ import annotations

from datetime import datetime
from typing import Any


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%d"):
        try:
            return datetime.strptime(value[:26], fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00").split("+")[0])
    except ValueError:
        return None


def _safe_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def extract_numero_controle(raw: dict[str, Any]) -> str:
    ctrl = raw.get("numeroControlePNCP") or raw.get("numeroControlePncp")
    if ctrl:
        return str(ctrl)
    seq = raw.get("sequencialCompra")
    orgao = raw.get("orgaoEntidade") or {}
    cnpj = orgao.get("cnpj") or orgao.get("cpf") or "unknown"
    ano = raw.get("anoCompra") or ""
    return f"{cnpj}-{ano}-{seq}"


def normalize_pncp_item(raw: dict[str, Any]) -> dict[str, Any]:
    orgao = raw.get("orgaoEntidade") or {}
    unidade = raw.get("unidadeOrgao") or {}
    modalidade = raw.get("modalidadeContratacao") or raw.get("modalidadeContratacaoPublica") or {}

    numero = extract_numero_controle(raw)
    objeto = (raw.get("objetoCompra") or raw.get("objeto") or "").strip()
    valor_est = _safe_float(raw.get("valorTotalEstimado"))
    valor_hom = _safe_float(raw.get("valorTotalHomologado"))

    qualidade = "ok"
    if not objeto or not orgao.get("razaoSocial"):
        qualidade = "incompleto"
    if valor_est is not None and valor_est < 0:
        qualidade = "suspeito"

    return {
        "numero_controle_pncp": numero,
        "sequencial_compra": raw.get("sequencialCompra"),
        "orgao_razao_social": orgao.get("razaoSocial") or orgao.get("nome") or "",
        "uf": unidade.get("ufSigla") or unidade.get("uf") or "",
        "municipio_ibge": str(unidade.get("codigoIbge") or unidade.get("municipioIbge") or "") or None,
        "objeto_compra": objeto,
        "modalidade": modalidade.get("descricao") or raw.get("modalidadeNome") or "",
        "modalidade_codigo": modalidade.get("codigo") or raw.get("codigoModalidadeContratacao"),
        "situacao": raw.get("situacaoCompraNome") or raw.get("situacao") or "",
        "data_publicacao": _parse_dt(raw.get("dataPublicacaoPncp") or raw.get("dataInclusao")),
        "data_abertura": _parse_dt(raw.get("dataAberturaProposta")),
        "data_encerramento": _parse_dt(raw.get("dataEncerramentoProposta")),
        "valor_total_estimado": valor_est,
        "valor_total_homologado": valor_hom,
        "link_sistema_origem": raw.get("linkSistemaOrigem"),
        "qualidade_dados": qualidade,
        "raw_json": raw,
    }
