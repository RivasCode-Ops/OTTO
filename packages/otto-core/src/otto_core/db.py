from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from otto_core.config import DB_PATH, DATA_DIR
from otto_core.migrations import apply_migrations
from otto_core.models import (
    Acompanhamento,
    AcompanhamentoUpdate,
    DecisaoUsuario,
    Oportunidade,
    OportunidadeEvento,
)
from otto_core.niche import classify_nicho
from otto_core.normalize import normalize_pncp_item
from otto_core.score import compute_score

SCHEMA = """
CREATE TABLE IF NOT EXISTS ingest_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  iniciado_em TEXT NOT NULL,
  finalizado_em TEXT,
  ufs TEXT,
  data_inicial TEXT,
  data_final TEXT,
  total_bruto INTEGER DEFAULT 0,
  total_normalizado INTEGER DEFAULT 0,
  total_novos INTEGER DEFAULT 0,
  total_atualizados INTEGER DEFAULT 0,
  erros INTEGER DEFAULT 0,
  mensagem TEXT
);

CREATE TABLE IF NOT EXISTS oportunidades (
  numero_controle_pncp TEXT PRIMARY KEY,
  sequencial_compra INTEGER,
  orgao_razao_social TEXT,
  uf TEXT,
  municipio_ibge TEXT,
  objeto_compra TEXT,
  modalidade TEXT,
  modalidade_codigo INTEGER,
  situacao TEXT,
  data_publicacao TEXT,
  data_abertura TEXT,
  data_encerramento TEXT,
  valor_total_estimado REAL,
  valor_total_homologado REAL,
  link_sistema_origem TEXT,
  nicho TEXT,
  confianca_classificacao TEXT,
  score_total REAL,
  score_detalhe TEXT,
  qualidade_dados TEXT,
  status_monitoramento TEXT,
  raw_json TEXT,
  coletado_em TEXT,
  atualizado_em TEXT
);

CREATE TABLE IF NOT EXISTS oportunidade_eventos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  numero_controle_pncp TEXT NOT NULL,
  tipo TEXT,
  campo TEXT,
  valor_anterior TEXT,
  valor_novo TEXT,
  detectado_em TEXT,
  FOREIGN KEY (numero_controle_pncp) REFERENCES oportunidades(numero_controle_pncp)
);

CREATE INDEX IF NOT EXISTS idx_oportunidades_score ON oportunidades(score_total DESC);
CREATE INDEX IF NOT EXISTS idx_oportunidades_nicho ON oportunidades(nicho);
CREATE INDEX IF NOT EXISTS idx_oportunidades_uf ON oportunidades(uf);
"""


def _now() -> str:
    return datetime.now(timezone.utc).replace(tzinfo=None).isoformat()


def _dt_str(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path or DB_PATH
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection | None = None) -> None:
    own = conn is None
    c = conn or get_connection()
    c.executescript(SCHEMA)
    apply_migrations(c)
    c.commit()
    if own:
        c.close()


_DECISOES: frozenset[str] = frozenset({"sem_decisao", "prosseguir", "nao_prosseguir"})
_FILTROS_ACOMP: frozenset[str] = frozenset(
    {"salvas", "interesse", "prosseguir", "nao_prosseguir", "todos"}
)


def _row_to_acomp(row: sqlite3.Row | None, numero: str) -> Acompanhamento:
    if row is None:
        return Acompanhamento(numero_controle_pncp=numero)
    return Acompanhamento(
        numero_controle_pncp=row["numero_controle_pncp"],
        salva=bool(row["salva"]),
        interesse=bool(row["interesse"]),
        decisao=row["decisao"] if row["decisao"] in _DECISOES else "sem_decisao",  # type: ignore[arg-type]
        observacoes=row["observacoes"] or "",
        justificativa=row["justificativa"] or "",
        atualizado_em=datetime.fromisoformat(row["atualizado_em"]) if row["atualizado_em"] else None,
    )


def get_acompanhamento(conn: sqlite3.Connection, numero: str) -> Acompanhamento:
    cur = conn.execute(
        "SELECT * FROM oportunidade_acompanhamento WHERE numero_controle_pncp = ?",
        (numero,),
    )
    return _row_to_acomp(cur.fetchone(), numero)


def upsert_acompanhamento(
    conn: sqlite3.Connection,
    numero: str,
    update: AcompanhamentoUpdate,
) -> Acompanhamento:
    if get_oportunidade(conn, numero) is None:
        raise ValueError("oportunidade_nao_encontrada")
    atual = get_acompanhamento(conn, numero)
    salva = atual.salva if update.salva is None else bool(update.salva)
    interesse = atual.interesse if update.interesse is None else bool(update.interesse)
    decisao: DecisaoUsuario = atual.decisao
    if update.decisao is not None:
        if update.decisao not in _DECISOES:
            raise ValueError("decisao_invalida")
        decisao = update.decisao
    observacoes = atual.observacoes if update.observacoes is None else update.observacoes
    justificativa = atual.justificativa if update.justificativa is None else update.justificativa
    agora = _now()
    conn.execute(
        """
        INSERT INTO oportunidade_acompanhamento (
          numero_controle_pncp, salva, interesse, decisao, observacoes, justificativa, atualizado_em
        ) VALUES (?,?,?,?,?,?,?)
        ON CONFLICT(numero_controle_pncp) DO UPDATE SET
          salva=excluded.salva,
          interesse=excluded.interesse,
          decisao=excluded.decisao,
          observacoes=excluded.observacoes,
          justificativa=excluded.justificativa,
          atualizado_em=excluded.atualizado_em
        """,
        (numero, int(salva), int(interesse), decisao, observacoes, justificativa, agora),
    )
    conn.commit()
    # DECISÃO (2026-11-04): marcar “Salvar” sincroniza estado_fluxo=salva quando o fluxo
    # ainda está em nao_avaliada/salva — não rebaixa análise/preparação/arquivada (README §5.4).
    if update.salva is True and salva:
        try:
            from otto_core.fluxo_store import get_fluxo, update_fluxo
            from otto_core.models import FluxoUpdate

            fluxo = get_fluxo(conn, numero)
            if fluxo.estado_fluxo in ("nao_avaliada", "salva"):
                update_fluxo(conn, numero, FluxoUpdate(estado_fluxo="salva"))
        except (ValueError, sqlite3.OperationalError):
            pass
    try:
        from otto_core.auditoria_store import registrar

        bits = []
        if update.salva is not None:
            bits.append(f"salva={salva}")
        if update.interesse is not None:
            bits.append(f"interesse={interesse}")
        if update.decisao is not None:
            bits.append(f"decisao={decisao}")
        if bits:
            registrar(conn, "acompanhamento", numero=numero, detalhe="; ".join(bits))
    except sqlite3.OperationalError:
        pass
    return get_acompanhamento(conn, numero)


def list_acompanhamento(
    conn: sqlite3.Connection,
    *,
    filtro: str = "todos",
    limit: int = 200,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """Lista oportunidades com acompanhamento. filtro: salvas|interesse|prosseguir|nao_prosseguir|todos."""
    f = filtro if filtro in _FILTROS_ACOMP else "todos"
    where = "WHERE 1=1"
    params: list[Any] = []
    if f == "salvas":
        where += " AND a.salva = 1"
    elif f == "interesse":
        where += " AND a.interesse = 1"
    elif f == "prosseguir":
        where += " AND a.decisao = 'prosseguir'"
    elif f == "nao_prosseguir":
        where += " AND a.decisao = 'nao_prosseguir'"
    else:
        where += " AND (a.salva = 1 OR a.interesse = 1 OR a.decisao != 'sem_decisao')"

    q = f"""
        SELECT o.*, a.salva AS ac_salva, a.interesse AS ac_interesse, a.decisao AS ac_decisao,
               a.observacoes AS ac_observacoes, a.justificativa AS ac_justificativa,
               a.atualizado_em AS ac_atualizado_em
        FROM oportunidade_acompanhamento a
        INNER JOIN oportunidades o ON o.numero_controle_pncp = a.numero_controle_pncp
        {where}
        ORDER BY a.atualizado_em DESC
        LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])
    rows = conn.execute(q, params).fetchall()
    raw_opps: list[Oportunidade] = []
    acomp_by_num: dict[str, Acompanhamento] = {}
    for r in rows:
        opp = _row_to_opp(r)
        # Lista: só município legível; evita mandar o JSON bruto inteiro.
        unidade = (opp.raw_json or {}).get("unidadeOrgao") or {}
        nome_mun = unidade.get("municipioNome")
        opp.raw_json = {"unidadeOrgao": {"municipioNome": nome_mun}} if nome_mun else {}
        raw_opps.append(opp)
        acomp_by_num[opp.numero_controle_pncp] = Acompanhamento(
            numero_controle_pncp=opp.numero_controle_pncp,
            salva=bool(r["ac_salva"]),
            interesse=bool(r["ac_interesse"]),
            decisao=r["ac_decisao"] if r["ac_decisao"] in _DECISOES else "sem_decisao",  # type: ignore[arg-type]
            observacoes=r["ac_observacoes"] or "",
            justificativa=r["ac_justificativa"] or "",
            atualizado_em=datetime.fromisoformat(r["ac_atualizado_em"]) if r["ac_atualizado_em"] else None,
        )
    return [
        {"oportunidade": opp, "acompanhamento": acomp_by_num[opp.numero_controle_pncp]}
        for opp in _enrich_lista_meta(conn, raw_opps)
    ]


def contagens_acompanhamento(conn: sqlite3.Connection) -> dict[str, int]:
    def _c(sql: str) -> int:
        return int(conn.execute(sql).fetchone()[0])

    out = {
        "salvas": _c("SELECT COUNT(*) FROM oportunidade_acompanhamento WHERE salva = 1"),
        "interesse": _c("SELECT COUNT(*) FROM oportunidade_acompanhamento WHERE interesse = 1"),
        "prosseguir": _c("SELECT COUNT(*) FROM oportunidade_acompanhamento WHERE decisao = 'prosseguir'"),
        "nao_prosseguir": _c(
            "SELECT COUNT(*) FROM oportunidade_acompanhamento WHERE decisao = 'nao_prosseguir'"
        ),
    }
    # Contagens de fluxo (se tabela existir)
    try:
        from otto_core.manual_store import contagens_fluxo

        for k, v in contagens_fluxo(conn).items():
            out[f"fluxo_{k}"] = v
    except sqlite3.OperationalError:
        pass
    return out


def _row_to_opp(row: sqlite3.Row) -> Oportunidade:
    score_det = json.loads(row["score_detalhe"]) if row["score_detalhe"] else {}
    raw = json.loads(row["raw_json"]) if row["raw_json"] else {}
    keys = row.keys()
    origem = "pncp"
    if "origem_registro" in keys and row["origem_registro"]:
        origem = row["origem_registro"]
    elif isinstance(raw, dict) and raw.get("origem_registro") == "manual":
        origem = "manual"
    return Oportunidade(
        numero_controle_pncp=row["numero_controle_pncp"],
        sequencial_compra=row["sequencial_compra"],
        orgao_razao_social=row["orgao_razao_social"] or "",
        uf=row["uf"] or "",
        municipio_ibge=row["municipio_ibge"],
        objeto_compra=row["objeto_compra"] or "",
        modalidade=row["modalidade"] or "",
        modalidade_codigo=row["modalidade_codigo"],
        situacao=row["situacao"] or "",
        data_publicacao=datetime.fromisoformat(row["data_publicacao"]) if row["data_publicacao"] else None,
        data_abertura=datetime.fromisoformat(row["data_abertura"]) if row["data_abertura"] else None,
        data_encerramento=datetime.fromisoformat(row["data_encerramento"]) if row["data_encerramento"] else None,
        data_esclarecimento=(
            datetime.fromisoformat(row["data_esclarecimento"])
            if "data_esclarecimento" in keys and row["data_esclarecimento"]
            else None
        ),
        data_impugnacao=(
            datetime.fromisoformat(row["data_impugnacao"])
            if "data_impugnacao" in keys and row["data_impugnacao"]
            else None
        ),
        valor_total_estimado=row["valor_total_estimado"],
        valor_total_homologado=row["valor_total_homologado"],
        link_sistema_origem=row["link_sistema_origem"],
        nicho=row["nicho"] or "outros",
        confianca_classificacao=row["confianca_classificacao"] or "nenhuma",
        score_total=row["score_total"] or 0,
        score_detalhe=score_det,  # type: ignore[arg-type]
        qualidade_dados=row["qualidade_dados"] or "ok",
        status_monitoramento=row["status_monitoramento"] or "ativo",
        origem_registro=origem,  # type: ignore[arg-type]
        raw_json=raw,
        coletado_em=datetime.fromisoformat(row["coletado_em"]) if row["coletado_em"] else None,
        atualizado_em=datetime.fromisoformat(row["atualizado_em"]) if row["atualizado_em"] else None,
    )


def atualizar_prazos_manuais(
    conn: sqlite3.Connection,
    numero: str,
    *,
    data_esclarecimento: str | None = None,
    data_impugnacao: str | None = None,
    limpar_esclarecimento: bool = False,
    limpar_impugnacao: bool = False,
) -> Oportunidade:
    """Atualiza prazos manuais de esclarecimento/impugnação (README §7)."""
    if get_oportunidade(conn, numero) is None:
        raise ValueError("oportunidade_nao_encontrada")
    row = conn.execute(
        "SELECT data_esclarecimento, data_impugnacao FROM oportunidades WHERE numero_controle_pncp = ?",
        (numero,),
    ).fetchone()
    if limpar_esclarecimento:
        esc = None
    elif data_esclarecimento is not None:
        esc = (data_esclarecimento or "").strip() or None
    else:
        esc = row["data_esclarecimento"] if row else None
    if limpar_impugnacao:
        imp = None
    elif data_impugnacao is not None:
        imp = (data_impugnacao or "").strip() or None
    else:
        imp = row["data_impugnacao"] if row else None
    agora = _now()
    conn.execute(
        """
        UPDATE oportunidades SET
          data_esclarecimento=?, data_impugnacao=?, atualizado_em=?
        WHERE numero_controle_pncp=?
        """,
        (esc, imp, agora, numero),
    )
    conn.commit()
    try:
        from otto_core.auditoria_store import registrar

        registrar(
            conn,
            "prazos_manuais",
            numero=numero,
            detalhe=f"esclarecimento={esc or '—'}; impugnacao={imp or '—'}",
        )
    except sqlite3.OperationalError:
        pass
    opp = get_oportunidade(conn, numero)
    assert opp is not None
    return opp


def count_orgao_historico(conn: sqlite3.Connection, orgao: str, nicho: str) -> int:
    cur = conn.execute(
        "SELECT COUNT(*) FROM oportunidades WHERE orgao_razao_social = ? AND nicho = ?",
        (orgao, nicho),
    )
    return int(cur.fetchone()[0])


def get_existing(conn: sqlite3.Connection, numero: str) -> sqlite3.Row | None:
    cur = conn.execute("SELECT * FROM oportunidades WHERE numero_controle_pncp = ?", (numero,))
    return cur.fetchone()


def _diff_events(old: sqlite3.Row, opp: Oportunidade) -> list[OportunidadeEvento]:
    events: list[OportunidadeEvento] = []
    checks = [
        ("situacao", old["situacao"], opp.situacao),
        ("valor_total_estimado", str(old["valor_total_estimado"]), str(opp.valor_total_estimado)),
        ("data_encerramento", old["data_encerramento"], _dt_str(opp.data_encerramento)),
    ]
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    for campo, anterior, novo in checks:
        if str(anterior or "") != str(novo or ""):
            events.append(
                OportunidadeEvento(
                    numero_controle_pncp=opp.numero_controle_pncp,
                    tipo="atualizacao",
                    campo=campo,
                    valor_anterior=str(anterior) if anterior else None,
                    valor_novo=str(novo) if novo else None,
                    detectado_em=now,
                )
            )
    return events


def upsert_oportunidade(conn: sqlite3.Connection, raw: dict[str, Any]) -> tuple[bool, list[OportunidadeEvento]]:
    data = normalize_pncp_item(raw)
    nicho, conf, _ = classify_nicho(data["objeto_compra"])
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    opp = Oportunidade(
        **{k: v for k, v in data.items() if k != "raw_json"},
        nicho=nicho,
        confianca_classificacao=conf,
        raw_json=data["raw_json"],
        coletado_em=now,
        atualizado_em=now,
    )
    hist = count_orgao_historico(conn, opp.orgao_razao_social, opp.nicho)
    opp = compute_score(opp, hist)

    existing = get_existing(conn, opp.numero_controle_pncp)
    events: list[OportunidadeEvento] = []
    is_new = existing is None

    if existing:
        events = _diff_events(existing, opp)
        coletado = existing["coletado_em"]
    else:
        coletado = _now()

    # PNCP upsert: origem_registro='pncp' em inserção; não sobrescreve se já for manual.
    cols = {r[1] for r in conn.execute("PRAGMA table_info(oportunidades)")}
    if "origem_registro" in cols:
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
            ON CONFLICT(numero_controle_pncp) DO UPDATE SET
              orgao_razao_social=excluded.orgao_razao_social,
              uf=excluded.uf,
              situacao=excluded.situacao,
              data_encerramento=excluded.data_encerramento,
              valor_total_estimado=excluded.valor_total_estimado,
              valor_total_homologado=excluded.valor_total_homologado,
              nicho=excluded.nicho,
              confianca_classificacao=excluded.confianca_classificacao,
              score_total=excluded.score_total,
              score_detalhe=excluded.score_detalhe,
              qualidade_dados=excluded.qualidade_dados,
              raw_json=excluded.raw_json,
              atualizado_em=excluded.atualizado_em
            WHERE oportunidades.origem_registro IS NULL OR oportunidades.origem_registro != 'manual'
            """,
            (
                opp.numero_controle_pncp,
                opp.sequencial_compra,
                opp.orgao_razao_social,
                opp.uf,
                opp.municipio_ibge,
                opp.objeto_compra,
                opp.modalidade,
                opp.modalidade_codigo,
                opp.situacao,
                _dt_str(opp.data_publicacao),
                _dt_str(opp.data_abertura),
                _dt_str(opp.data_encerramento),
                opp.valor_total_estimado,
                opp.valor_total_homologado,
                opp.link_sistema_origem,
                opp.nicho,
                opp.confianca_classificacao,
                opp.score_total,
                json.dumps(opp.score_detalhe.model_dump(), ensure_ascii=False),
                opp.qualidade_dados,
                opp.status_monitoramento,
                json.dumps(opp.raw_json, ensure_ascii=False),
                coletado,
                _now(),
                "pncp",
            ),
        )
    else:
        conn.execute(
            """
            INSERT INTO oportunidades (
              numero_controle_pncp, sequencial_compra, orgao_razao_social, uf, municipio_ibge,
              objeto_compra, modalidade, modalidade_codigo, situacao,
              data_publicacao, data_abertura, data_encerramento,
              valor_total_estimado, valor_total_homologado, link_sistema_origem,
              nicho, confianca_classificacao, score_total, score_detalhe,
              qualidade_dados, status_monitoramento, raw_json, coletado_em, atualizado_em
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(numero_controle_pncp) DO UPDATE SET
              orgao_razao_social=excluded.orgao_razao_social,
              uf=excluded.uf,
              situacao=excluded.situacao,
              data_encerramento=excluded.data_encerramento,
              valor_total_estimado=excluded.valor_total_estimado,
              valor_total_homologado=excluded.valor_total_homologado,
              nicho=excluded.nicho,
              confianca_classificacao=excluded.confianca_classificacao,
              score_total=excluded.score_total,
              score_detalhe=excluded.score_detalhe,
              qualidade_dados=excluded.qualidade_dados,
              raw_json=excluded.raw_json,
              atualizado_em=excluded.atualizado_em
            """,
            (
                opp.numero_controle_pncp,
                opp.sequencial_compra,
                opp.orgao_razao_social,
                opp.uf,
                opp.municipio_ibge,
                opp.objeto_compra,
                opp.modalidade,
                opp.modalidade_codigo,
                opp.situacao,
                _dt_str(opp.data_publicacao),
                _dt_str(opp.data_abertura),
                _dt_str(opp.data_encerramento),
                opp.valor_total_estimado,
                opp.valor_total_homologado,
                opp.link_sistema_origem,
                opp.nicho,
                opp.confianca_classificacao,
                opp.score_total,
                json.dumps(opp.score_detalhe.model_dump(), ensure_ascii=False),
                opp.qualidade_dados,
                opp.status_monitoramento,
                json.dumps(opp.raw_json, ensure_ascii=False),
                coletado,
                _now(),
            ),
        )

    for ev in events:
        conn.execute(
            """
            INSERT INTO oportunidade_eventos
            (numero_controle_pncp, tipo, campo, valor_anterior, valor_novo, detectado_em)
            VALUES (?,?,?,?,?,?)
            """,
            (ev.numero_controle_pncp, ev.tipo, ev.campo, ev.valor_anterior, ev.valor_novo, ev.detectado_em.isoformat()),
        )

    return is_new, events


# DECISÃO (2026-11-04): lista geral LICITAR ordena por publicação/prazo, não por score TI.
# Ver docs/licitar-acompanhamento e README.txt §6.3.
ORDENACAO_LISTA = frozenset({"publicacao", "prazo"})


def _enrich_lista_meta(conn: sqlite3.Connection, items: list[Oportunidade]) -> list[Oportunidade]:
    """Anexa categoria principal (classificação ou nicho) e contagem de documentos locais."""
    if not items:
        return items
    nums = [o.numero_controle_pncp for o in items]
    ph = ",".join("?" * len(nums))
    docs: dict[str, int] = {}
    try:
        for r in conn.execute(
            f"""
            SELECT numero_controle_pncp, COUNT(*) AS c
            FROM oportunidade_documentos
            WHERE numero_controle_pncp IN ({ph})
            GROUP BY numero_controle_pncp
            """,
            nums,
        ):
            docs[str(r["numero_controle_pncp"])] = int(r["c"])
    except sqlite3.OperationalError:
        pass
    cats: dict[str, str] = {}
    try:
        for r in conn.execute(
            f"""
            SELECT numero_controle_pncp, setor, categoria
            FROM oportunidade_classificacoes
            WHERE numero_controle_pncp IN ({ph})
            ORDER BY id
            """,
            nums,
        ):
            key = str(r["numero_controle_pncp"])
            if key in cats:
                continue
            label = (r["categoria"] or r["setor"] or "").strip()
            if label:
                cats[key] = label
    except sqlite3.OperationalError:
        pass
    out: list[Oportunidade] = []
    for o in items:
        num = o.numero_controle_pncp
        cat = cats.get(num) or (o.nicho if o.nicho and o.nicho != "outros" else "")
        out.append(
            o.model_copy(
                update={
                    "categoria_principal": cat,
                    "documentos_count": docs.get(num, 0),
                }
            )
        )
    return out


def _oportunidades_where(
    *,
    nicho: str | None = None,
    uf: str | None = None,
    excluir_arquivadas: bool = True,
) -> tuple[str, list[Any]]:
    """Cláusula WHERE compartilhada por list/count (alias `o`)."""
    q = " WHERE 1=1"
    params: list[Any] = []
    if nicho:
        q += " AND o.nicho = ?"
        params.append(nicho)
    if uf:
        q += " AND o.uf = ?"
        params.append(uf)
    if excluir_arquivadas:
        # Arquivadas saem da lista geral (README §5.4); ainda acessíveis na vista Fluxo.
        q += (
            " AND NOT EXISTS ("
            " SELECT 1 FROM oportunidade_fluxo f"
            " WHERE f.numero_controle_pncp = o.numero_controle_pncp"
            " AND f.estado_fluxo = 'arquivada')"
        )
    return q, params


def count_oportunidades(
    conn: sqlite3.Connection,
    *,
    nicho: str | None = None,
    uf: str | None = None,
    excluir_arquivadas: bool = True,
) -> int:
    where, params = _oportunidades_where(
        nicho=nicho, uf=uf, excluir_arquivadas=excluir_arquivadas
    )
    row = conn.execute(
        f"SELECT COUNT(*) AS c FROM oportunidades o{where}", params
    ).fetchone()
    return int(row["c"])


def list_oportunidades(
    conn: sqlite3.Connection,
    *,
    nicho: str | None = None,
    uf: str | None = None,
    ordenacao: str = "publicacao",
    limit: int = 100,
    offset: int = 0,
    excluir_arquivadas: bool = True,
) -> list[Oportunidade]:
    """Lista oportunidades. ordenacao: publicacao (mais recente) | prazo (encerramento mais próximo)."""
    ordem = ordenacao if ordenacao in ORDENACAO_LISTA else "publicacao"
    where, params = _oportunidades_where(
        nicho=nicho, uf=uf, excluir_arquivadas=excluir_arquivadas
    )
    q = f"SELECT o.* FROM oportunidades o{where}"
    # NULLS LAST: em SQLite, `col IS NULL` coloca ausentes depois (0 antes de 1).
    if ordem == "prazo":
        q += " ORDER BY o.data_encerramento IS NULL ASC, o.data_encerramento ASC LIMIT ? OFFSET ?"
    else:
        q += " ORDER BY o.data_publicacao IS NULL ASC, o.data_publicacao DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    cur = conn.execute(q, params)
    return _enrich_lista_meta(conn, [_row_to_opp(r) for r in cur.fetchall()])


def get_cobertura_coleta(conn: sqlite3.Connection) -> dict[str, Any]:
    """Metadados da coleta real (config + última execução + o que há no banco)."""
    from otto_core.config import load_yaml

    cfg = load_yaml("ingest.yaml")
    ufs_cfg = list(cfg.get("ufs") or [])
    modalidades_cfg = [int(m) for m in (cfg.get("modalidades") or [])]
    janela = int(cfg.get("janela_dias_padrao") or 7)

    last = conn.execute(
        "SELECT * FROM ingest_runs ORDER BY id DESC LIMIT 1"
    ).fetchone()
    ultima: dict[str, Any] | None = None
    if last:
        ultima = {
            "id": last["id"],
            "iniciado_em": last["iniciado_em"],
            "finalizado_em": last["finalizado_em"],
            "ufs": last["ufs"],
            "data_inicial": last["data_inicial"],
            "data_final": last["data_final"],
            "total_bruto": last["total_bruto"],
            "total_novos": last["total_novos"],
            "total_atualizados": last["total_atualizados"],
            "erros": last["erros"],
            "mensagem": last["mensagem"],
        }

    total = int(conn.execute("SELECT COUNT(*) AS c FROM oportunidades").fetchone()["c"])
    ufs_db = [
        r["uf"]
        for r in conn.execute(
            "SELECT DISTINCT uf FROM oportunidades WHERE uf IS NOT NULL AND TRIM(uf) != '' ORDER BY uf"
        )
    ]
    por_nicho = [
        {"nicho": r["nicho"] or "outros", "quantidade": int(r["c"])}
        for r in conn.execute(
            "SELECT nicho, COUNT(*) AS c FROM oportunidades GROUP BY nicho ORDER BY c DESC"
        )
    ]

    modalidade_nome = {6: "Pregão eletrônico"}
    modalidades_legivel = [
        modalidade_nome.get(m, f"Código {m}") for m in modalidades_cfg
    ]

    return {
        "aviso": (
            "A lista mostra apenas o que já foi coletado e gravado neste computador. "
            "“Todos os setores” significa todos os nichos presentes nesses dados — "
            "não todas as oportunidades do Brasil."
        ),
        "fonte": "PNCP (Portal Nacional de Contratações Públicas)",
        "config_coleta": {
            "ufs": ufs_cfg,
            "modalidades_codigos": modalidades_cfg,
            "modalidades": modalidades_legivel,
            "janela_dias_padrao": janela,
        },
        "ultima_execucao": ultima,
        "banco": {
            "total_oportunidades": total,
            "ufs_presentes": ufs_db,
            "por_nicho": por_nicho,
        },
        "ordenacao": {
            "padrao": "publicacao",
            "campo_publicacao": "data_publicacao",
            "campo_prazo": "data_encerramento",
            "rotulo_prazo": "Prazo de encerramento da proposta",
            "sem_prazo": "Registros sem data de encerramento ficam no final na ordenação por prazo.",
        },
    }


def get_oportunidade(conn: sqlite3.Connection, numero: str) -> Oportunidade | None:
    row = get_existing(conn, numero)
    return _row_to_opp(row) if row else None


def list_eventos(conn: sqlite3.Connection, numero: str) -> list[dict]:
    cur = conn.execute(
        "SELECT * FROM oportunidade_eventos WHERE numero_controle_pncp = ? ORDER BY detectado_em DESC",
        (numero,),
    )
    return [dict(r) for r in cur.fetchall()]


def count_recent_eventos(
    conn: sqlite3.Connection,
    *,
    uf: str | None = None,
    nicho: str | None = None,
    days: int = 7,
) -> int:
    q = """
        SELECT COUNT(*) AS c FROM oportunidade_eventos e
        INNER JOIN oportunidades o ON o.numero_controle_pncp = e.numero_controle_pncp
        WHERE date(e.detectado_em) >= date('now', ?)
    """
    params: list[Any] = [f"-{days} days"]
    if nicho:
        q += " AND o.nicho = ?"
        params.append(nicho)
    if uf:
        q += " AND o.uf = ?"
        params.append(uf)
    return int(conn.execute(q, params).fetchone()["c"])


def list_recent_eventos(
    conn: sqlite3.Connection,
    *,
    uf: str | None = None,
    nicho: str | None = None,
    days: int = 7,
    limit: int = 8,
) -> list[dict]:
    q = """
        SELECT e.*, o.orgao_razao_social, o.objeto_compra, o.uf, o.nicho
        FROM oportunidade_eventos e
        INNER JOIN oportunidades o ON o.numero_controle_pncp = e.numero_controle_pncp
        WHERE date(e.detectado_em) >= date('now', ?)
    """
    params: list[Any] = [f"-{days} days"]
    if nicho:
        q += " AND o.nicho = ?"
        params.append(nicho)
    if uf:
        q += " AND o.uf = ?"
        params.append(uf)
    q += " ORDER BY e.detectado_em DESC LIMIT ?"
    params.append(limit)
    return [dict(r) for r in conn.execute(q, params).fetchall()]


def kpis(conn: sqlite3.Connection, *, nicho: str | None = None, uf: str | None = None) -> dict:
    where = "WHERE 1=1"
    params: list[Any] = []
    if nicho:
        where += " AND nicho = ?"
        params.append(nicho)
    if uf:
        where += " AND uf = ?"
        params.append(uf)

    cur = conn.execute(f"SELECT COUNT(*) as c, COALESCE(SUM(valor_total_estimado),0) as v FROM oportunidades {where}", params)
    row = cur.fetchone()
    total = int(row["c"])
    pipeline = float(row["v"] or 0)

    cur2 = conn.execute(
        f"""
        SELECT COUNT(*) as c FROM oportunidades {where}
        AND data_encerramento IS NOT NULL
        AND date(data_encerramento) <= date('now', '+7 days')
        AND date(data_encerramento) >= date('now')
        """,
        params,
    )
    vencendo = int(cur2.fetchone()["c"])

    cur3 = conn.execute(
        f"""
        SELECT * FROM oportunidades {where}
        ORDER BY data_publicacao IS NULL ASC, data_publicacao DESC
        LIMIT 10
        """,
        params,
    )
    top = [_row_to_opp(r) for r in cur3.fetchall()]

    return {
        "total": total,
        "valor_pipeline": pipeline,
        "vencendo_7_dias": vencendo,
        "top10": top,
    }


def get_alertas(
    conn: sqlite3.Connection,
    *,
    uf: str | None = None,
    nicho: str | None = "ti_software",
    desde: str | None = None,
    confianca: str = "alta",
    limit: int = 10,
) -> dict[str, Any]:
    """Alertas V1: novas alta confiança (modo TI), mudanças recentes, prazos urgentes."""
    if not desde:
        desde = (datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=24)).isoformat()

    base = "WHERE 1=1"
    params: list[Any] = []
    if nicho:
        base += " AND nicho = ?"
        params.append(nicho)
    if uf:
        base += " AND uf = ?"
        params.append(uf)

    novas_q = f"""
        SELECT * FROM oportunidades {base}
        AND confianca_classificacao = ?
        AND coletado_em >= ?
        ORDER BY score_total DESC LIMIT ?
    """
    novas_params = [*params, confianca, desde, limit]
    novas_rows = conn.execute(novas_q, novas_params).fetchall()
    novas = [_row_to_opp(r) for r in novas_rows]

    cur_n = conn.execute(
        f"SELECT COUNT(*) AS c FROM oportunidades {base} AND confianca_classificacao = ? AND coletado_em >= ?",
        [*params, confianca, desde],
    )
    total_novas = int(cur_n.fetchone()["c"])

    mudancas = count_recent_eventos(conn, uf=uf, nicho=nicho, days=7)
    mudancas_items = list_recent_eventos(conn, uf=uf, nicho=nicho, days=7, limit=limit)

    urgente_q = f"""
        SELECT COUNT(*) AS c FROM oportunidades {base}
        AND confianca_classificacao = ?
        AND data_encerramento IS NOT NULL
        AND date(data_encerramento) <= date('now', '+3 days')
        AND date(data_encerramento) >= date('now')
    """
    vencendo_urgente = int(conn.execute(urgente_q, [*params, confianca]).fetchone()["c"])

    items: list[dict[str, Any]] = []
    for o in novas:
        items.append(
            {
                "tipo": "nova",
                "titulo": "Nova oportunidade TI",
                "numero_controle_pncp": o.numero_controle_pncp,
                "orgao_razao_social": o.orgao_razao_social,
                "objeto_compra": (o.objeto_compra or "")[:160],
                "score_total": o.score_total,
            }
        )
    for e in mudancas_items[: max(0, limit - len(items))]:
        items.append(
            {
                "tipo": "mudanca",
                "titulo": f"Mudança: {e.get('campo', 'campo')}",
                "numero_controle_pncp": e["numero_controle_pncp"],
                "orgao_razao_social": e.get("orgao_razao_social", ""),
                "campo": e.get("campo"),
                "valor_anterior": e.get("valor_anterior"),
                "valor_novo": e.get("valor_novo"),
            }
        )

    return {
        "desde": desde,
        "novas_alta_confianca": total_novas,
        "mudancas_7d": mudancas,
        "vencendo_urgente_3d": vencendo_urgente,
        "total": total_novas + mudancas + vencendo_urgente,
        "novas": [_row_to_opp(r).model_dump() for r in novas_rows[:limit]],
        "items": items[:limit],
    }
