"""Cenários financeiros locais (README §11) — sem chamar estimativa incompleta de lucro."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from otto_core.models import CenarioFinanceiro, CenarioFinanceiroUpsert

CAMPOS_CUSTO = (
    "frete",
    "deslocamento",
    "mao_obra",
    "despesas_operacionais",
    "tributos",
    "outros_custos",
    "contingencia",
)


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _parse(v: str | None) -> datetime | None:
    if not v:
        return None
    try:
        return datetime.fromisoformat(v)
    except ValueError:
        return None


def _calc(row: sqlite3.Row | dict) -> CenarioFinanceiro:
    def g(k: str) -> float | None:
        if isinstance(row, dict):
            return row.get(k)
        return row[k]

    avisos: list[str] = []
    receita = g("receita_estimada")
    qtd = g("quantidade")
    unit = g("custo_unitario")
    custos_partes: list[float] = []
    custo_itens: float | None = None
    if qtd is not None and unit is not None:
        custo_itens = float(qtd) * float(unit)
        custos_partes.append(custo_itens)
    elif qtd is not None or unit is not None:
        avisos.append(
            "Quantidade ou custo unitário informado sem o outro — custo de itens não calculado."
        )

    for k in CAMPOS_CUSTO:
        v = g(k)
        if v is not None:
            custos_partes.append(float(v))

    custos_reg = sum(custos_partes) if custos_partes else None
    incompleto = False
    if receita is None:
        incompleto = True
        avisos.append("Receita estimada não informada (permanece desconhecida — não é zero).")
    if custos_reg is None:
        incompleto = True
        avisos.append("Nenhum custo registrado ainda.")
    if g("escopo_parcial"):
        avisos.append(
            "Escopo parcial marcado: não use o valor global da oportunidade como receita "
            "sem informar a parte pretendida."
        )
    if not (g("premissas") or "").strip():
        avisos.append("Premissas vazias — registre hipóteses usadas neste cenário.")
        incompleto = True

    saldo = None
    margem = None
    if receita is not None and custos_reg is not None:
        saldo = float(receita) - float(custos_reg)
        if float(receita) != 0:
            margem = (saldo / float(receita)) * 100.0
        if incompleto:
            avisos.append(
                "Há saldo sobre custos registrados, mas o cenário ainda está incompleto — "
                "não chame isso de lucro líquido."
            )
        else:
            avisos.append(
                "Saldo estimado sobre os custos registrados (não é lucro líquido contábil)."
            )
    elif receita is not None or custos_reg is not None:
        incompleto = True

    # Resultados realizados (informados pelo usuário) — separados do estimado.
    try:
        receita_real = g("receita_realizada")
        custos_real = g("custos_realizados")
    except (IndexError, KeyError):
        receita_real = None
        custos_real = None

    saldo_real = None
    if receita_real is not None and custos_real is not None:
        saldo_real = float(receita_real) - float(custos_real)
        avisos.append(
            "Saldo realizado = receita realizada − custos realizados (informados por você). "
            "Não confundir com o saldo estimado."
        )
        if receita is not None and abs(float(receita_real) - float(receita)) > 1e-9:
            avisos.append(
                f"Receita realizada difere da estimada "
                f"({float(receita_real):.2f} vs {float(receita):.2f})."
            )
        if custos_reg is not None and abs(float(custos_real) - float(custos_reg)) > 1e-9:
            avisos.append(
                f"Custos realizados diferem dos custos estimados registrados "
                f"({float(custos_real):.2f} vs {float(custos_reg):.2f})."
            )
    elif receita_real is not None or custos_real is not None:
        avisos.append(
            "Resultado realizado parcial: informe receita e custos realizados para o saldo."
        )

    try:
        prazo_des = str(g("prazo_desembolso") or "")
        prazo_rec = str(g("prazo_recebimento") or "")
    except (IndexError, KeyError):
        prazo_des, prazo_rec = "", ""

    # Necessidade de caixa: custos registrados que precisam sair antes do recebimento.
    # Sem prazos, igualamos aos custos registrados e avisamos a limitação.
    necessidade = None
    if custos_reg is not None:
        necessidade = float(custos_reg)
        if prazo_des or prazo_rec:
            avisos.append(
                "Necessidade de caixa estimada = custos registrados (base informada). "
                f"Desembolso: {prazo_des or 'não informado'}; "
                f"recebimento: {prazo_rec or 'não informado'}."
            )
        else:
            avisos.append(
                "Necessidade de caixa estimada = custos registrados. "
                "Informe prazos de desembolso/recebimento para contextualizar o timing "
                "(não é fluxo de caixa diário)."
            )

    return CenarioFinanceiro(
        id=int(g("id") or 0),
        numero_controle_pncp=str(g("numero_controle_pncp") or ""),
        nome=str(g("nome") or "Cenário 1"),
        receita_estimada=receita,
        quantidade=qtd,
        custo_unitario=unit,
        frete=g("frete"),
        deslocamento=g("deslocamento"),
        mao_obra=g("mao_obra"),
        despesas_operacionais=g("despesas_operacionais"),
        tributos=g("tributos"),
        outros_custos=g("outros_custos"),
        contingencia=g("contingencia"),
        premissas=str(g("premissas") or ""),
        escopo_parcial=bool(g("escopo_parcial")),
        receita_realizada=receita_real,
        custos_realizados=custos_real,
        prazo_desembolso=prazo_des,
        prazo_recebimento=prazo_rec,
        atualizado_em=_parse(str(g("atualizado_em")) if g("atualizado_em") else None),
        custos_registrados=custos_reg,
        saldo_sobre_custos_registrados=saldo,
        margem_estimada_pct=margem,
        saldo_realizado=saldo_real,
        necessidade_caixa_estimada=necessidade,
        incompleto=incompleto,
        avisos=avisos,
    )


def list_cenarios(conn: sqlite3.Connection, numero: str) -> list[CenarioFinanceiro]:
    rows = conn.execute(
        "SELECT * FROM cenarios_financeiros WHERE numero_controle_pncp = ? ORDER BY id",
        (numero,),
    ).fetchall()
    return [_calc(r) for r in rows]


def fluxo_caixa_timeline(conn: sqlite3.Connection, numero: str) -> dict:
    """Linha do tempo simples a partir dos prazos dos cenários (sem regras tributárias)."""
    eventos: list[dict] = []
    for c in list_cenarios(conn, numero):
        if c.prazo_desembolso:
            eventos.append(
                {
                    "data": c.prazo_desembolso,
                    "tipo": "desembolso",
                    "cenario": c.nome,
                    "valor": c.necessidade_caixa_estimada,
                }
            )
        if c.prazo_recebimento:
            eventos.append(
                {
                    "data": c.prazo_recebimento,
                    "tipo": "recebimento",
                    "cenario": c.nome,
                    "valor": c.receita_estimada if c.receita_realizada is None else c.receita_realizada,
                }
            )
    eventos.sort(key=lambda e: (e["data"] or "", e["tipo"]))
    return {
        "eventos": eventos,
        "aviso": (
            "Linha do tempo local pelos prazos informados nos cenários. "
            "Não aplica regras tributárias fixas (decisão pendente)."
        ),
    }


def upsert_cenario(
    conn: sqlite3.Connection,
    numero: str,
    body: CenarioFinanceiroUpsert,
    cenario_id: int | None = None,
) -> CenarioFinanceiro:
    opp = conn.execute(
        "SELECT 1 FROM oportunidades WHERE numero_controle_pncp = ?", (numero,)
    ).fetchone()
    if not opp:
        raise ValueError("Oportunidade não encontrada.")
    agora = _now()
    set_fields = body.model_fields_set

    def pick(name: str, default: object = None) -> object:
        if name in set_fields:
            return getattr(body, name)
        return default

    if cenario_id is None:
        cur = conn.execute(
            """
            INSERT INTO cenarios_financeiros (
              numero_controle_pncp, nome, receita_estimada, quantidade, custo_unitario,
              frete, deslocamento, mao_obra, despesas_operacionais, tributos,
              outros_custos, contingencia, premissas, escopo_parcial,
              receita_realizada, custos_realizados, prazo_desembolso, prazo_recebimento,
              atualizado_em
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                numero,
                body.nome or "Cenário 1",
                body.receita_estimada,
                body.quantidade,
                body.custo_unitario,
                body.frete,
                body.deslocamento,
                body.mao_obra,
                body.despesas_operacionais,
                body.tributos,
                body.outros_custos,
                body.contingencia,
                body.premissas or "",
                1 if body.escopo_parcial else 0,
                body.receita_realizada,
                body.custos_realizados,
                body.prazo_desembolso or "",
                body.prazo_recebimento or "",
                agora,
            ),
        )
        cid = int(cur.lastrowid)
    else:
        row = conn.execute(
            "SELECT * FROM cenarios_financeiros WHERE id = ? AND numero_controle_pncp = ?",
            (cenario_id, numero),
        ).fetchone()
        if not row:
            raise ValueError("Cenário não encontrado.")
        rkeys = row.keys()
        receita_real = pick(
            "receita_realizada",
            row["receita_realizada"] if "receita_realizada" in rkeys else None,
        )
        custos_real = pick(
            "custos_realizados",
            row["custos_realizados"] if "custos_realizados" in rkeys else None,
        )
        prazo_des = pick(
            "prazo_desembolso",
            row["prazo_desembolso"] if "prazo_desembolso" in rkeys else "",
        )
        prazo_rec = pick(
            "prazo_recebimento",
            row["prazo_recebimento"] if "prazo_recebimento" in rkeys else "",
        )
        conn.execute(
            """
            UPDATE cenarios_financeiros SET
              nome=?, receita_estimada=?, quantidade=?, custo_unitario=?,
              frete=?, deslocamento=?, mao_obra=?, despesas_operacionais=?, tributos=?,
              outros_custos=?, contingencia=?, premissas=?, escopo_parcial=?,
              receita_realizada=?, custos_realizados=?,
              prazo_desembolso=?, prazo_recebimento=?, atualizado_em=?
            WHERE id=?
            """,
            (
                body.nome or "Cenário 1",
                body.receita_estimada,
                body.quantidade,
                body.custo_unitario,
                body.frete,
                body.deslocamento,
                body.mao_obra,
                body.despesas_operacionais,
                body.tributos,
                body.outros_custos,
                body.contingencia,
                body.premissas or "",
                1 if body.escopo_parcial else 0,
                receita_real,
                custos_real,
                prazo_des or "",
                prazo_rec or "",
                agora,
                cenario_id,
            ),
        )
        cid = cenario_id
    conn.commit()
    r = conn.execute("SELECT * FROM cenarios_financeiros WHERE id = ?", (cid,)).fetchone()
    return _calc(r)
