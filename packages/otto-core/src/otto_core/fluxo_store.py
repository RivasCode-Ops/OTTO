"""Estados de preparação / participação / resultados (distintos)."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from otto_core.models import EstadoFluxo, FluxoOportunidade, FluxoUpdate, ResultadoEtapa

ESTADOS: set[str] = {
    "nao_avaliada",
    "salva",
    "em_analise",
    "aguardando_informacoes",
    "em_preparacao",
    "participacao_registrada",
    "em_acompanhamento",
    "encerrada",
    "arquivada",
}
RESULTADOS: set[str] = {
    "nao_informado",
    "nao_aplicavel",
    "pendente",
    "sim",
    "nao",
    "em_andamento",
    "concluido",
}

AVISO = (
    "Preparação, participação e resultados são situações distintas. "
    "Nada é enviado a plataformas de licitação."
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


def _row(r: sqlite3.Row) -> FluxoOportunidade:
    keys = set(r.keys())
    return FluxoOportunidade(
        numero_controle_pncp=r["numero_controle_pncp"],
        estado_fluxo=r["estado_fluxo"],  # type: ignore[arg-type]
        resultado_disputa=r["resultado_disputa"],  # type: ignore[arg-type]
        resultado_contratacao=r["resultado_contratacao"],  # type: ignore[arg-type]
        resultado_execucao=r["resultado_execucao"],  # type: ignore[arg-type]
        resultado_recebimento=r["resultado_recebimento"],  # type: ignore[arg-type]
        notas_resultado=r["notas_resultado"] or "",
        tempo_preparacao_horas=(
            r["tempo_preparacao_horas"] if "tempo_preparacao_horas" in keys else None
        ),
        custo_preparacao=r["custo_preparacao"] if "custo_preparacao" in keys else None,
        atualizado_em=_parse(r["atualizado_em"]),
        aviso=AVISO,
    )


def get_fluxo(conn: sqlite3.Connection, numero: str) -> FluxoOportunidade:
    opp = conn.execute(
        "SELECT 1 FROM oportunidades WHERE numero_controle_pncp = ?", (numero,)
    ).fetchone()
    if not opp:
        raise ValueError("Oportunidade não encontrada.")
    r = conn.execute(
        "SELECT * FROM oportunidade_fluxo WHERE numero_controle_pncp = ?", (numero,)
    ).fetchone()
    if r:
        return _row(r)
    agora = _now()
    conn.execute(
        """
        INSERT INTO oportunidade_fluxo (
          numero_controle_pncp, estado_fluxo, resultado_disputa, resultado_contratacao,
          resultado_execucao, resultado_recebimento, notas_resultado, atualizado_em
        ) VALUES (?,?,?,?,?,?,?,?)
        """,
        (numero, "nao_avaliada", "nao_informado", "nao_informado", "nao_informado", "nao_informado", "", agora),
    )
    conn.commit()
    return get_fluxo(conn, numero)


def update_fluxo(conn: sqlite3.Connection, numero: str, body: FluxoUpdate) -> FluxoOportunidade:
    atual = get_fluxo(conn, numero)
    estado: EstadoFluxo = body.estado_fluxo or atual.estado_fluxo
    if estado not in ESTADOS:
        raise ValueError("estado_fluxo inválido")
    rd: ResultadoEtapa = body.resultado_disputa or atual.resultado_disputa
    rc: ResultadoEtapa = body.resultado_contratacao or atual.resultado_contratacao
    re: ResultadoEtapa = body.resultado_execucao or atual.resultado_execucao
    rr: ResultadoEtapa = body.resultado_recebimento or atual.resultado_recebimento
    for label, val in (
        ("resultado_disputa", rd),
        ("resultado_contratacao", rc),
        ("resultado_execucao", re),
        ("resultado_recebimento", rr),
    ):
        if val not in RESULTADOS:
            raise ValueError(f"{label} inválido")
    notas = body.notas_resultado if body.notas_resultado is not None else atual.notas_resultado
    tempo = (
        body.tempo_preparacao_horas
        if body.tempo_preparacao_horas is not None
        else atual.tempo_preparacao_horas
    )
    custo = (
        body.custo_preparacao if body.custo_preparacao is not None else atual.custo_preparacao
    )
    agora = _now()
    # Colunas 009: se a migração ainda não rodou, atualiza só o núcleo.
    cols = {
        r[1] for r in conn.execute("PRAGMA table_info(oportunidade_fluxo)").fetchall()
    }
    if "tempo_preparacao_horas" in cols and "custo_preparacao" in cols:
        conn.execute(
            """
            UPDATE oportunidade_fluxo SET
              estado_fluxo=?, resultado_disputa=?, resultado_contratacao=?,
              resultado_execucao=?, resultado_recebimento=?, notas_resultado=?,
              tempo_preparacao_horas=?, custo_preparacao=?, atualizado_em=?
            WHERE numero_controle_pncp=?
            """,
            (estado, rd, rc, re, rr, notas or "", tempo, custo, agora, numero),
        )
    else:
        conn.execute(
            """
            UPDATE oportunidade_fluxo SET
              estado_fluxo=?, resultado_disputa=?, resultado_contratacao=?,
              resultado_execucao=?, resultado_recebimento=?, notas_resultado=?, atualizado_em=?
            WHERE numero_controle_pncp=?
            """,
            (estado, rd, rc, re, rr, notas or "", agora, numero),
        )
    conn.commit()
    try:
        from otto_core.auditoria_store import registrar

        registrar(conn, "fluxo", numero=numero, detalhe=f"estado={estado}")
    except sqlite3.OperationalError:
        pass
    return get_fluxo(conn, numero)


def listar_resultados(conn: sqlite3.Connection, *, limit: int = 200, offset: int = 0) -> dict:
    """Vista agregada de resultados (README §13) — local, sem envio externo."""
    from otto_core.db import _enrich_lista_meta, _row_to_opp

    rows = conn.execute(
        """
        SELECT o.*, f.estado_fluxo, f.resultado_disputa, f.resultado_contratacao,
               f.resultado_execucao, f.resultado_recebimento, f.notas_resultado,
               f.tempo_preparacao_horas, f.custo_preparacao, f.atualizado_em AS fluxo_atualizado_em
        FROM oportunidade_fluxo f
        INNER JOIN oportunidades o ON o.numero_controle_pncp = f.numero_controle_pncp
        WHERE f.estado_fluxo IN ('participacao_registrada','em_acompanhamento','encerrada')
           OR f.resultado_disputa != 'nao_informado'
           OR f.resultado_contratacao != 'nao_informado'
           OR f.resultado_execucao != 'nao_informado'
           OR f.resultado_recebimento != 'nao_informado'
           OR IFNULL(f.tempo_preparacao_horas, -1) >= 0
           OR IFNULL(f.custo_preparacao, -1) >= 0
        ORDER BY f.atualizado_em DESC
        LIMIT ? OFFSET ?
        """,
        (limit, offset),
    ).fetchall()
    opps = _enrich_lista_meta(conn, [_row_to_opp(r) for r in rows])
    by_num = {o.numero_controle_pncp: o for o in opps}
    items = []
    for r in rows:
        num = r["numero_controle_pncp"]
        items.append(
            {
                "oportunidade": by_num[num],
                "estado_fluxo": r["estado_fluxo"],
                "resultado_disputa": r["resultado_disputa"],
                "resultado_contratacao": r["resultado_contratacao"],
                "resultado_execucao": r["resultado_execucao"],
                "resultado_recebimento": r["resultado_recebimento"],
                "notas_resultado": r["notas_resultado"] or "",
                "tempo_preparacao_horas": r["tempo_preparacao_horas"],
                "custo_preparacao": r["custo_preparacao"],
                "atualizado_em": r["fluxo_atualizado_em"],
            }
        )
    return {
        "items": items,
        "count": len(items),
        "aviso": (
            "Resultados locais de disputa/contratação/execução/recebimento. "
            "Não consultam plataformas externas nesta versão."
        ),
    }
