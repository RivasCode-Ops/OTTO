"""Cadastro manual de oportunidades — distinto da coleta PNCP."""
from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any

from otto_core.models import Oportunidade, ScoreDetalhe

ORIGENS = frozenset({"pncp", "manual"})


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _parse_opt(v: str | None) -> str | None:
    t = (v or "").strip()
    return t or None


def criar_oportunidade_manual(
    conn: sqlite3.Connection,
    *,
    objeto_compra: str,
    orgao_razao_social: str = "",
    uf: str = "",
    municipio: str = "",
    modalidade: str = "",
    situacao: str = "Cadastrada manualmente",
    data_publicacao: str | None = None,
    data_encerramento: str | None = None,
    valor_total_estimado: float | None = None,
    link: str | None = None,
    numero_controle: str | None = None,
) -> Oportunidade:
    objeto = (objeto_compra or "").strip()
    if not objeto:
        raise ValueError("Objeto da oportunidade é obrigatório.")
    uf_n = (uf or "").strip().upper()[:2]
    agora = _now()
    numero = (numero_controle or "").strip() or f"MANUAL-{uuid.uuid4().hex[:12].upper()}"
    if conn.execute(
        "SELECT 1 FROM oportunidades WHERE numero_controle_pncp = ?", (numero,)
    ).fetchone():
        raise ValueError("Já existe oportunidade com este identificador.")

    score = ScoreDetalhe()
    raw = {
        "origem_registro": "manual",
        "cadastrado_em": agora,
        "aviso": "Registro criado manualmente neste computador — não veio da coleta PNCP.",
    }
    conn.execute(
        """
        INSERT INTO oportunidades (
          numero_controle_pncp, sequencial_compra, orgao_razao_social, uf, municipio_ibge,
          objeto_compra, modalidade, modalidade_codigo, situacao,
          data_publicacao, data_abertura, data_encerramento,
          valor_total_estimado, valor_total_homologado, link_sistema_origem,
          nicho, confianca_classificacao, score_total, score_detalhe,
          qualidade_dados, status_monitoramento, raw_json, coletado_em, atualizado_em,
          origem_registro
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            numero,
            None,
            (orgao_razao_social or "").strip(),
            uf_n,
            (municipio or "").strip() or None,
            objeto,
            (modalidade or "").strip(),
            None,
            (situacao or "Cadastrada manualmente").strip(),
            _parse_opt(data_publicacao) or agora,
            None,
            _parse_opt(data_encerramento),
            valor_total_estimado,
            None,
            _parse_opt(link),
            "outros",
            "nenhuma",
            0,
            json.dumps(score.model_dump()),
            "ok",
            "ativo",
            json.dumps(raw, ensure_ascii=False),
            agora,
            agora,
            "manual",
        ),
    )
    # Fluxo inicial: não avaliada
    conn.execute(
        """
        INSERT OR IGNORE INTO oportunidade_fluxo (
          numero_controle_pncp, estado_fluxo, resultado_disputa, resultado_contratacao,
          resultado_execucao, resultado_recebimento, notas_resultado, atualizado_em
        ) VALUES (?,?,?,?,?,?,?,?)
        """,
        (numero, "nao_avaliada", "nao_informado", "nao_informado", "nao_informado", "nao_informado", "", agora),
    )
    conn.commit()
    from otto_core.db import get_oportunidade

    opp = get_oportunidade(conn, numero)
    assert opp is not None
    return opp


def listar_por_fluxo(
    conn: sqlite3.Connection,
    estado: str,
    *,
    limit: int = 100,
    offset: int = 0,
) -> list[dict[str, Any]]:
    from otto_core.fluxo_store import ESTADOS
    from otto_core.db import _row_to_opp

    if estado not in ESTADOS:
        raise ValueError("estado_fluxo inválido")
    rows = conn.execute(
        """
        SELECT o.*
        FROM oportunidades o
        INNER JOIN oportunidade_fluxo f ON f.numero_controle_pncp = o.numero_controle_pncp
        WHERE f.estado_fluxo = ?
        ORDER BY o.atualizado_em DESC
        LIMIT ? OFFSET ?
        """,
        (estado, limit, offset),
    ).fetchall()
    from otto_core.db import _enrich_lista_meta

    opps = _enrich_lista_meta(conn, [_row_to_opp(r) for r in rows])
    return [
        {
            "oportunidade": opp,
            "estado_fluxo": estado,
        }
        for opp in opps
    ]


def contagens_fluxo(conn: sqlite3.Connection) -> dict[str, int]:
    from otto_core.fluxo_store import ESTADOS

    out = {e: 0 for e in sorted(ESTADOS)}
    for r in conn.execute(
        "SELECT estado_fluxo, COUNT(*) AS c FROM oportunidade_fluxo GROUP BY estado_fluxo"
    ):
        if r["estado_fluxo"] in out:
            out[r["estado_fluxo"]] = int(r["c"])
    return out


def importar_manuais_json(conn: sqlite3.Connection, payload: Any) -> dict[str, Any]:
    """Importa lista JSON de oportunidades manuais (README §6.1) — não mistura origem PNCP."""
    if isinstance(payload, dict) and "items" in payload:
        items = payload.get("items") or []
    elif isinstance(payload, list):
        items = payload
    else:
        raise ValueError("JSON deve ser uma lista ou {\"items\": [...]}.")
    if not isinstance(items, list):
        raise ValueError("Campo items deve ser uma lista.")
    criados: list[str] = []
    erros: list[dict[str, Any]] = []
    for i, raw in enumerate(items):
        if not isinstance(raw, dict):
            erros.append({"indice": i, "erro": "Item deve ser objeto."})
            continue
        try:
            valor = raw.get("valor_total_estimado")
            valor_f = float(valor) if valor is not None and str(valor).strip() != "" else None
            opp = criar_oportunidade_manual(
                conn,
                objeto_compra=str(raw.get("objeto_compra") or raw.get("objeto") or ""),
                orgao_razao_social=str(raw.get("orgao_razao_social") or raw.get("orgao") or ""),
                uf=str(raw.get("uf") or ""),
                municipio=str(raw.get("municipio") or raw.get("municipio_ibge") or ""),
                modalidade=str(raw.get("modalidade") or ""),
                situacao=str(raw.get("situacao") or "Cadastrada manualmente"),
                data_publicacao=raw.get("data_publicacao"),
                data_encerramento=raw.get("data_encerramento"),
                valor_total_estimado=valor_f,
                link=raw.get("link_sistema_origem") or raw.get("link"),
                numero_controle=raw.get("numero_controle_pncp") or raw.get("numero_controle"),
            )
            criados.append(opp.numero_controle_pncp)
        except (ValueError, TypeError) as e:
            erros.append({"indice": i, "erro": str(e)})
    try:
        from otto_core.auditoria_store import registrar

        registrar(
            conn,
            "import_manual_json",
            detalhe=f"criados={len(criados)}; erros={len(erros)}",
        )
    except sqlite3.OperationalError:
        pass
    return {
        "criados": criados,
        "erros": erros,
        "aviso": (
            "Importação manual concluída. Registros ficam com origem “manual” "
            "(não alteram nem substituem coleta PNCP)."
        ),
    }
