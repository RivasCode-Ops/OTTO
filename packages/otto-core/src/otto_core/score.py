from __future__ import annotations

from datetime import datetime, timezone

from otto_core.config import load_yaml
from otto_core.models import Oportunidade, ScoreDetalhe


def _pontos_faixa(valor: float | None, faixas: list[dict]) -> tuple[float, str]:
    if valor is None or valor <= 0:
        return 10.0, "Valor não informado"
    for faixa in faixas:
        max_v = faixa.get("max")
        if max_v is None or valor <= float(max_v):
            pts = float(faixa["pontos"])
            label = f"R$ {valor:,.0f}".replace(",", ".")
            if max_v:
                label += f" (até R$ {float(max_v):,.0f})".replace(",", ".")
            else:
                label += " (faixa alta)"
            return pts, label
    return 10.0, "Valor baixo"


def _pontos_urgencia(data_encerramento: datetime | None) -> tuple[float, str]:
    if not data_encerramento:
        return 20.0, "Prazo não informado"
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    dias = (data_encerramento - now).days
    cfg = load_yaml("score.yaml")
    for faixa in cfg.get("urgencia_dias", []):
        max_d = faixa.get("max")
        if max_d is None or dias <= int(max_d):
            if dias < 0:
                return 100.0, f"Vencida há {-dias} dia(s)"
            if dias == 0:
                return 100.0, "Vence hoje"
            return float(faixa["pontos"]), f"Vence em {dias} dia(s)"
    return 20.0, "Prazo distante"


def _pontos_nicho(nicho: str, confianca: str) -> tuple[float, str]:
    cfg = load_yaml("score.yaml").get("nicho", {})
    if nicho == "ti_software":
        if confianca == "alta":
            return float(cfg.get("ti_alta", 100)), "TI — confiança alta"
        return float(cfg.get("ti_baixa", 60)), "TI — confiança baixa"
    return float(cfg.get("outros", 10)), "Fora do nicho TI"


def _pontos_recorrencia(orgao: str, count: int) -> tuple[float, str]:
    cfg = load_yaml("score.yaml").get("recorrencia", {})
    por = float(cfg.get("por_ocorrencia", 15))
    max_pts = float(cfg.get("max_pontos", 100))
    pts = min(max_pts, count * por)
    return pts, f"{count} ocorrência(s) históricas do órgão"


def compute_score(opp: Oportunidade, orgao_historico: int = 0) -> Oportunidade:
    cfg = load_yaml("score.yaml")
    pesos = cfg.get("pesos", {})

    pv, lv = _pontos_faixa(opp.valor_total_estimado, cfg.get("valor_faixas", []))
    pu, lu = _pontos_urgencia(opp.data_encerramento)
    pn, ln = _pontos_nicho(opp.nicho, opp.confianca_classificacao)
    pr, lr = _pontos_recorrencia(opp.orgao_razao_social, orgao_historico)

    wv = float(pesos.get("valor", 0.4))
    wu = float(pesos.get("urgencia", 0.3))
    wn = float(pesos.get("nicho", 0.2))
    wr = float(pesos.get("recorrencia", 0.1))

    total = pv * wv + pu * wu + pn * wn + pr * wr
    opp.score_total = round(min(100.0, max(0.0, total)), 1)
    opp.score_detalhe = ScoreDetalhe(
        valor=round(pv * wv, 1),
        urgencia=round(pu * wu, 1),
        nicho=round(pn * wn, 1),
        recorrencia=round(pr * wr, 1),
        labels={"valor": lv, "urgencia": lu, "nicho": ln, "recorrencia": lr},
    )
    return opp
