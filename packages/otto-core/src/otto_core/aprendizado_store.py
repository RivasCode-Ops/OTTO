"""
Aprendizado local a partir do histórico.

DECISÃO (2026-11-06): tudo no computador; sem nuvem; sem fine-tune de pesos.
- Resumo para o usuário entender ações/resultados.
- Contexto opcional no prompt da próxima análise local (heurística),
  só quando houver decisões suficientes (aplicar/rejeitar).
Não inventa fatos do edital; evidência e preservação de natureza=usuario continuam obrigatórias.
"""
from __future__ import annotations

import sqlite3
from typing import Any

# Mínimo de sugestões decididas (aplicada+rejeitada) para influenciar o prompt.
MIN_DECISOES_PARA_INFLUENCIA = 3


def resumo_aprendizado(conn: sqlite3.Connection) -> dict[str, Any]:
    """Agrega histórico local em insights legíveis + estado da influência no prompt."""
    acoes = _contar_auditoria(conn)
    ia = _contar_ia(conn)
    resultados = _contar_resultados(conn)
    ctx = contexto_para_analise_ia(conn)
    insights = _montar_insights(acoes, ia, resultados, ctx)

    return {
        "acoes": acoes,
        "ia_sugestoes": ia,
        "resultados": resultados,
        "influencia_analise": {
            "ativa": bool(ctx.get("ativo")),
            "decisoes": ctx.get("decisoes", 0),
            "minimo": MIN_DECISOES_PARA_INFLUENCIA,
            "chaves_preferidas": ctx.get("chaves_preferidas") or [],
            "chaves_evitar": ctx.get("chaves_evitar") or [],
            "resumo_prompt": (ctx.get("bloco_prompt") or "")[:400],
        },
        "insights": insights,
        "aviso": (
            "Resumo local neste computador. Não treina pesos do modelo nem envia dados. "
            "Com histórico suficiente, a próxima análise local recebe um bloco de preferências "
            "no prompt (heurística). Continua exigindo evidência e revisão humana; "
            "campos de origem usuário não são sobrescritos."
        ),
        "nuvem": False,
        "altera_modelo": False,
        "influencia_prompt_local": True,
    }


def contexto_para_analise_ia(conn: sqlite3.Connection) -> dict[str, Any]:
    """
    Preferências derivadas do histórico para o prompt da análise local.
    Retorna ativo=False se houver poucas decisões.
    """
    vazio: dict[str, Any] = {
        "ativo": False,
        "decisoes": 0,
        "chaves_preferidas": [],
        "chaves_evitar": [],
        "tipos_preferidos": [],
        "bloco_prompt": "",
        "motivo_inativo": f"Menos de {MIN_DECISOES_PARA_INFLUENCIA} sugestões decididas (aplicar/rejeitar).",
    }
    if not _table_exists(conn, "analise_ia_sugestoes"):
        vazio["motivo_inativo"] = "Sem tabela de sugestões IA."
        return vazio

    rows = conn.execute(
        """
        SELECT tipo, chave, estado, COUNT(*) AS n
        FROM analise_ia_sugestoes
        WHERE estado IN ('aplicada', 'rejeitada')
        GROUP BY tipo, chave, estado
        """
    ).fetchall()
    # chave -> {aplicada, rejeitada}
    por_chave: dict[str, dict[str, int]] = {}
    por_tipo_app: dict[str, int] = {}
    decisoes = 0
    for r in rows:
        n = int(r["n"])
        decisoes += n
        tipo = (r["tipo"] or "").strip() or "?"
        chave = (r["chave"] or "").strip()
        estado = r["estado"]
        if tipo == "campo" and chave:
            bucket = por_chave.setdefault(chave, {"aplicada": 0, "rejeitada": 0})
            bucket[estado] = bucket.get(estado, 0) + n
        if estado == "aplicada":
            por_tipo_app[tipo] = por_tipo_app.get(tipo, 0) + n

    if decisoes < MIN_DECISOES_PARA_INFLUENCIA:
        vazio["decisoes"] = decisoes
        return vazio

    preferidas: list[str] = []
    evitar: list[str] = []
    for chave, c in sorted(por_chave.items()):
        ap = c.get("aplicada", 0)
        rj = c.get("rejeitada", 0)
        if ap >= 2 and ap > rj:
            preferidas.append(chave)
        if rj >= 2 and rj > ap:
            evitar.append(chave)

    tipos = sorted(por_tipo_app.keys(), key=lambda t: (-por_tipo_app[t], t))
    linhas = [
        "Preferências do usuário neste computador (histórico local de aplicar/rejeitar):",
        f"- Decisões usadas: {decisoes}.",
    ]
    if preferidas:
        linhas.append(
            "- Campos que o usuário costuma ACEITAR quando bem evidentes: "
            + ", ".join(preferidas[:8])
            + ". Priorize extrair estes se estiverem no texto com trecho fiel."
        )
    if evitar:
        linhas.append(
            "- Campos que o usuário costuma REJEITAR: "
            + ", ".join(evitar[:8])
            + ". Só sugira se o trecho no documento for inequívoco; na dúvida, OMITA."
        )
    if tipos:
        linhas.append(
            "- Tipos mais aceitos: " + ", ".join(f"{t}({por_tipo_app[t]})" for t in tipos[:4]) + "."
        )
    linhas.extend(
        [
            "- Continua proibido inventar fatos, trechos ou páginas.",
            "- Se não houver citação literal no documento, omita o item.",
            "- Isto é preferência de foco, não autorização para inventar.",
        ]
    )
    bloco = "\n".join(linhas)
    return {
        "ativo": True,
        "decisoes": decisoes,
        "chaves_preferidas": preferidas[:8],
        "chaves_evitar": evitar[:8],
        "tipos_preferidos": tipos[:4],
        "bloco_prompt": bloco,
        "motivo_inativo": "",
    }


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    r = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (name,),
    ).fetchone()
    return r is not None


def _contar_auditoria(conn: sqlite3.Connection) -> dict[str, Any]:
    if not _table_exists(conn, "auditoria_acoes"):
        return {"total": 0, "por_acao": [], "ultimas": []}
    total = int(conn.execute("SELECT COUNT(*) FROM auditoria_acoes").fetchone()[0])
    por = conn.execute(
        """
        SELECT acao, COUNT(*) AS n
        FROM auditoria_acoes
        GROUP BY acao
        ORDER BY n DESC, acao
        LIMIT 20
        """
    ).fetchall()
    ultimas = conn.execute(
        """
        SELECT id, acao, numero_controle_pncp, detalhe, criado_em
        FROM auditoria_acoes
        ORDER BY id DESC
        LIMIT 12
        """
    ).fetchall()
    return {
        "total": total,
        "por_acao": [{"acao": r["acao"], "n": int(r["n"])} for r in por],
        "ultimas": [
            {
                "id": int(r["id"]),
                "acao": r["acao"],
                "numero_controle_pncp": r["numero_controle_pncp"],
                "detalhe": r["detalhe"] or "",
                "criado_em": r["criado_em"],
            }
            for r in ultimas
        ],
    }


def _contar_ia(conn: sqlite3.Connection) -> dict[str, Any]:
    if not _table_exists(conn, "analise_ia_sugestoes"):
        return {
            "total": 0,
            "aplicadas": 0,
            "rejeitadas": 0,
            "pendentes": 0,
            "taxa_aceitacao": None,
            "por_tipo_aplicadas": [],
            "amostras_aplicadas": [],
            "amostras_rejeitadas": [],
        }
    rows = conn.execute(
        """
        SELECT estado, COUNT(*) AS n
        FROM analise_ia_sugestoes
        GROUP BY estado
        """
    ).fetchall()
    por_estado = {r["estado"]: int(r["n"]) for r in rows}
    aplicadas = por_estado.get("aplicada", 0)
    rejeitadas = por_estado.get("rejeitada", 0)
    pendentes = por_estado.get("pendente", 0)
    decididas = aplicadas + rejeitadas
    taxa = round(aplicadas / decididas, 3) if decididas else None

    por_tipo = conn.execute(
        """
        SELECT tipo, COUNT(*) AS n
        FROM analise_ia_sugestoes
        WHERE estado = 'aplicada'
        GROUP BY tipo
        ORDER BY n DESC
        """
    ).fetchall()

    def _amostra(estado: str, lim: int = 5) -> list[dict[str, Any]]:
        rs = conn.execute(
            """
            SELECT id, tipo, chave, titulo, valor, estado, criado_em, numero_controle_pncp
            FROM analise_ia_sugestoes
            WHERE estado = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (estado, lim),
        ).fetchall()
        return [
            {
                "id": int(r["id"]),
                "tipo": r["tipo"],
                "chave": r["chave"] or "",
                "titulo": (r["titulo"] or "")[:120],
                "valor": (r["valor"] or "")[:160],
                "numero_controle_pncp": r["numero_controle_pncp"],
                "criado_em": r["criado_em"],
            }
            for r in rs
        ]

    return {
        "total": aplicadas + rejeitadas + pendentes + sum(
            v for k, v in por_estado.items() if k not in {"aplicada", "rejeitada", "pendente"}
        ),
        "aplicadas": aplicadas,
        "rejeitadas": rejeitadas,
        "pendentes": pendentes,
        "taxa_aceitacao": taxa,
        "por_tipo_aplicadas": [{"tipo": r["tipo"], "n": int(r["n"])} for r in por_tipo],
        "amostras_aplicadas": _amostra("aplicada"),
        "amostras_rejeitadas": _amostra("rejeitada"),
    }


def _contar_resultados(conn: sqlite3.Connection) -> dict[str, Any]:
    if not _table_exists(conn, "oportunidade_fluxo"):
        return {"com_resultado": 0, "por_disputa": [], "por_estado_fluxo": []}

    def _group(col: str) -> list[dict[str, Any]]:
        # Whitelist — nunca interpolar input externo.
        if col not in {"resultado_disputa", "estado_fluxo"}:
            raise ValueError("coluna inválida")
        rs = conn.execute(
            f"""
            SELECT {col} AS k, COUNT(*) AS n
            FROM oportunidade_fluxo
            WHERE {col} IS NOT NULL AND {col} != '' AND {col} != 'nao_informado'
            GROUP BY {col}
            ORDER BY n DESC
            LIMIT 12
            """
        ).fetchall()
        return [{"valor": r["k"], "n": int(r["n"])} for r in rs]

    com = int(
        conn.execute(
            """
            SELECT COUNT(*) FROM oportunidade_fluxo
            WHERE resultado_disputa != 'nao_informado'
               OR resultado_contratacao != 'nao_informado'
               OR resultado_execucao != 'nao_informado'
               OR resultado_recebimento != 'nao_informado'
            """
        ).fetchone()[0]
    )
    return {
        "com_resultado": com,
        "por_disputa": _group("resultado_disputa"),
        "por_estado_fluxo": _group("estado_fluxo"),
    }


def _montar_insights(
    acoes: dict[str, Any],
    ia: dict[str, Any],
    resultados: dict[str, Any],
    ctx: dict[str, Any] | None = None,
) -> list[str]:
    out: list[str] = []
    if acoes["total"] == 0 and ia["total"] == 0 and resultados["com_resultado"] == 0:
        out.append(
            "Ainda há pouco histórico. Use o app (salvar, analisar, aplicar/rejeitar IA, "
            "registrar resultados) para este resumo ganhar sentido."
        )
        return out

    if acoes["total"]:
        top = acoes["por_acao"][0] if acoes["por_acao"] else None
        out.append(f"Você registrou {acoes['total']} ação(ões) na auditoria local.")
        if top:
            out.append(f"Ação mais frequente: “{top['acao']}” ({top['n']}×).")

    decididas = ia["aplicadas"] + ia["rejeitadas"]
    if decididas:
        pct = int(round((ia["taxa_aceitacao"] or 0) * 100))
        out.append(
            f"Sugestões de IA decididas: {decididas} "
            f"({ia['aplicadas']} aplicadas, {ia['rejeitadas']} rejeitadas; "
            f"aceitação ≈ {pct}%)."
        )
        if ia["aplicadas"] and ia["rejeitadas"] == 0:
            out.append(
                "Você ainda não rejeitou sugestões — revise se está aceitando demais sem checar o trecho."
            )
        elif ia["rejeitadas"] and ia["aplicadas"] == 0:
            out.append(
                "Você só rejeitou sugestões até agora — o fluxo manual da ficha continua sendo a fonte da verdade."
            )
        if ia["por_tipo_aplicadas"]:
            tipos = ", ".join(f"{t['tipo']} ({t['n']})" for t in ia["por_tipo_aplicadas"][:4])
            out.append(f"Tipos mais aplicados: {tipos}.")
    elif ia["pendentes"]:
        out.append(
            f"Há {ia['pendentes']} sugestão(ões) de IA ainda pendente(s) de revisão."
        )

    if resultados["com_resultado"]:
        out.append(
            f"{resultados['com_resultado']} oportunidade(s) com algum resultado "
            f"de disputa/contratação/execução/recebimento informado."
        )
        if resultados["por_disputa"]:
            d = resultados["por_disputa"][0]
            out.append(f"Resultado de disputa mais comum: “{d['valor']}” ({d['n']}×).")
    else:
        out.append(
            "Ainda não há resultados de participação preenchidos — o aprendizado de "
            "“o que deu certo” fica incompleto até você registrar o desfecho."
        )

    ctx = ctx or {}
    if ctx.get("ativo"):
        pref = ", ".join(ctx.get("chaves_preferidas") or []) or "—"
        evit = ", ".join(ctx.get("chaves_evitar") or []) or "—"
        out.append(
            f"Influência no prompt da próxima análise: ATIVA "
            f"(preferir: {pref}; só com evidência forte se evitar: {evit})."
        )
    else:
        out.append(
            "Influência no prompt ainda inativa — "
            + (ctx.get("motivo_inativo") or "histórico insuficiente.")
        )
    out.append(
        "Não há fine-tune de pesos: só preferências no prompt local + suas regras de evidência."
    )
    return out
