"""Órgãos, classificações multissetoriais, visões e indicadores (README §12).

Concorrência: só com registros reais de participantes/resultados.
Neste banco PNCP local esses registros não existem — ver concorrencia_status().

DECISÃO (2026-11-06): entidade órgão ampliada — CNPJ só dígitos (várias fontes no JSON);
mesma razão social normalizada sem CNPJ une ao CNPJ já visto em outra oportunidade.
Não une nomes só “parecidos” (Pref. vs Prefeitura).
"""
from __future__ import annotations

import json
import re
import sqlite3
import unicodedata
from datetime import datetime, timezone
from typing import Any

from otto_core.models import Oportunidade

# DECISÃO (2026-11-06): §12.2 — prioridade local explicável (frequência, categorias,
# valores/período, resultados do usuário, condições operacionais). Sem reputação.

# Mapeamento nicho (coluna oportunidades) → classificação multissetorial.
NICHO_PARA_SETOR: dict[str, tuple[str, str, str]] = {
    "ti_software": ("ti", "software_e_servicos", ""),
    "saude_medicamentos": ("saude_medicamentos", "medicamentos_hospitalar", ""),
    "obras_engenharia": ("obras_engenharia", "obras_e_reforma", ""),
    "passagens_viagens": ("passagens_viagens", "agenciamento", ""),
    "alimentos_merenda": ("alimentos_merenda", "merenda_e_generos", ""),
    "material_escritorio_papelaria": ("material_escritorio_papelaria", "expediente", ""),
    "limpeza_conservacao": ("limpeza_conservacao", "limpeza", ""),
    "veiculos_combustiveis": ("veiculos_combustiveis", "frota_e_combustivel", ""),
    "outros": ("outros", "nao_classificado", ""),
}

_CNPJ_DIGITS_RE = re.compile(r"\D+")


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _parse_raw(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        d = json.loads(raw)
        return d if isinstance(d, dict) else {}
    except json.JSONDecodeError:
        return {}


def normalizar_cnpj(valor: str | None) -> str | None:
    """Mantém só dígitos. Aceita 11 (CPF) ou 14 (CNPJ); outros comprimentos com ≥8 dígitos
    preservam a chave (dados de teste / variantes), sem inventar dígitos."""
    if not valor:
        return None
    digits = _CNPJ_DIGITS_RE.sub("", str(valor))
    if len(digits) in (11, 14) or len(digits) >= 8:
        return digits
    return None


def normalizar_nome_orgao(nome: str | None) -> str:
    """Upper + sem acento + espaços colapsados — chave quando não há CNPJ."""
    t = (nome or "").strip()
    if not t:
        return ""
    folded = unicodedata.normalize("NFKD", t)
    ascii_ = folded.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", ascii_).strip().upper()


def _extrair_cnpj_raw(raw: dict[str, Any]) -> str | None:
    """CNPJ/CPF em orgaoEntidade, unidadeOrgao e campos soltos comuns no PNCP."""
    candidatos: list[Any] = []
    ent = raw.get("orgaoEntidade")
    if isinstance(ent, dict):
        candidatos.extend(
            [
                ent.get("cnpj"),
                ent.get("cnpjFormatado"),
                ent.get("ni"),
                ent.get("cpf"),
            ]
        )
    uo = raw.get("unidadeOrgao")
    if isinstance(uo, dict):
        candidatos.extend([uo.get("cnpj"), uo.get("cnpjFormatado")])
    candidatos.extend([raw.get("cnpj"), raw.get("cnpjOrgao"), raw.get("ni")])
    for c in candidatos:
        n = normalizar_cnpj(c if c is None else str(c))
        if n:
            return n
    return None


def _extrair_nome_raw(orgao_razao: str, raw: dict[str, Any]) -> str:
    ent = raw.get("orgaoEntidade")
    if isinstance(ent, dict):
        for k in ("razaoSocial", "nome", "nomeExibicao"):
            v = (ent.get(k) or "").strip()
            if v:
                return v
    uo = raw.get("unidadeOrgao")
    if isinstance(uo, dict):
        v = (uo.get("nomeUnidade") or "").strip()
        if v and not (orgao_razao or "").strip():
            return v
    return (orgao_razao or "").strip()


def orgao_chave_de_row(orgao_razao: str, raw_json: str | None) -> tuple[str, str | None, str]:
    """Chave provisória (sem merge entre oportunidades). Preferência: CNPJ normalizado."""
    raw = _parse_raw(raw_json)
    nome = _extrair_nome_raw(orgao_razao, raw)
    cnpj = _extrair_cnpj_raw(raw)
    if cnpj:
        return f"cnpj:{cnpj}", cnpj, nome or orgao_razao
    safe = normalizar_nome_orgao(nome or orgao_razao)
    if not safe:
        return "nome:DESCONHECIDO", None, nome or orgao_razao or "Desconhecido"
    return f"nome:{safe}", None, nome or orgao_razao


def _mapa_nome_para_cnpj(rows: list[Any]) -> dict[str, str]:
    """Se alguma oportunidade da mesma razão social tem CNPJ, as sem CNPJ usam esse CNPJ."""
    out: dict[str, str] = {}
    for r in rows:
        _, cnpj, nome = orgao_chave_de_row(r["orgao_razao_social"] or "", r["raw_json"])
        if not cnpj:
            continue
        nn = normalizar_nome_orgao(nome)
        if nn:
            out[nn] = cnpj
    return out


def resolver_orgao_chave(
    orgao_razao: str,
    raw_json: str | None,
    nome_para_cnpj: dict[str, str] | None = None,
) -> tuple[str, str | None, str]:
    """Chave final após merge nome→CNPJ conhecido no recorte."""
    chave, cnpj, nome = orgao_chave_de_row(orgao_razao, raw_json)
    if cnpj:
        return chave, cnpj, nome
    nn = normalizar_nome_orgao(nome)
    if nome_para_cnpj and nn and nn in nome_para_cnpj:
        c = nome_para_cnpj[nn]
        return f"cnpj:{c}", c, nome
    return chave, cnpj, nome


def _buscar_anotacao(
    conn: sqlite3.Connection,
    orgao_chave: str,
    *,
    cnpj: str | None = None,
    nome: str | None = None,
) -> sqlite3.Row | None:
    """Tenta chave canônica e aliases (nome: / cnpj:) para não perder nota após merge."""
    candidatos = [orgao_chave]
    if cnpj:
        candidatos.append(f"cnpj:{cnpj}")
    nn = normalizar_nome_orgao(nome)
    if nn:
        candidatos.append(f"nome:{nn}")
    seen: set[str] = set()
    for k in candidatos:
        if not k or k in seen:
            continue
        seen.add(k)
        row = conn.execute(
            "SELECT * FROM orgao_anotacoes WHERE orgao_chave = ?", (k,)
        ).fetchone()
        if row:
            return row
    return None


def _municipio(raw: dict[str, Any], ibge: str | None) -> str:
    uo = raw.get("unidadeOrgao") or {}
    if isinstance(uo, dict) and uo.get("municipioNome"):
        return str(uo["municipioNome"])
    return ibge or ""


def ensure_classificacoes_basicas(conn: sqlite3.Connection) -> int:
    """Garante ao menos uma classificação automática a partir do nicho legado."""
    agora = _now()
    rows = conn.execute(
        "SELECT numero_controle_pncp, nicho FROM oportunidades"
    ).fetchall()
    criadas = 0
    for r in rows:
        existe = conn.execute(
            "SELECT 1 FROM oportunidade_classificacoes WHERE numero_controle_pncp = ? LIMIT 1",
            (r["numero_controle_pncp"],),
        ).fetchone()
        if existe:
            continue
        setor, cat, sub = NICHO_PARA_SETOR.get(
            r["nicho"] or "outros", ("outros", "nao_classificado", "")
        )
        conn.execute(
            """
            INSERT OR IGNORE INTO oportunidade_classificacoes (
              numero_controle_pncp, setor, categoria, subcategoria,
              origem, revisado_pelo_usuario, atualizado_em
            ) VALUES (?,?,?,?,?,?,?)
            """,
            (r["numero_controle_pncp"], setor, cat, sub, "automatico", 0, agora),
        )
        criadas += 1
    conn.commit()
    return criadas


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (name,),
    ).fetchone()
    return row is not None


def _dias_desde_iso(iso: str | None) -> int | None:
    if not iso:
        return None
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", iso.strip())
    if not m:
        return None
    try:
        dt = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None
    hoje = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    return (hoje - dt.replace(hour=0, minute=0, second=0, microsecond=0)).days


def _prazo_ainda_aberto(iso: str | None) -> bool:
    """True se data_encerramento é hoje ou futura (civil local)."""
    d = _dias_desde_iso(iso)
    if d is None:
        return False
    return d <= 0  # dias desde encerramento ≤ 0 ⇒ ainda não passou / é hoje


def calcular_prioridade_orgao(
    *,
    n_oportunidades: int,
    n_setores: int,
    valor_estimado_soma: float | None,
    data_max_publicacao: str | None,
    n_abertas: int,
    n_interesse_ou_salva: int,
    n_participacao: int,
    n_resultado: int,
    tem_anotacao: bool,
) -> dict[str, Any]:
    """§12.2 — score local + motivos explícitos. Sem reputação."""
    score = 0
    motivos: list[str] = []

    pts_freq = min(40, max(0, n_oportunidades) * 4)
    if pts_freq:
        score += pts_freq
        motivos.append(f"{n_oportunidades} oportunidade(s) no banco local")

    pts_cat = min(15, max(0, n_setores) * 5)
    if pts_cat:
        score += pts_cat
        motivos.append(f"{n_setores} setor(es)/categoria(s) observados")

    if valor_estimado_soma is not None and valor_estimado_soma > 0:
        score += 10
        motivos.append("Há valor estimado informado em ao menos uma compra")

    dias = _dias_desde_iso(data_max_publicacao)
    if dias is not None and dias <= 30:
        score += 10
        motivos.append("Publicação recente (≤30 dias)")

    if n_abertas > 0:
        score += min(10, n_abertas * 2)
        motivos.append(f"{n_abertas} com prazo de proposta ainda aberto")

    if n_interesse_ou_salva > 0:
        score += min(15, n_interesse_ou_salva * 5)
        motivos.append(f"{n_interesse_ou_salva} marcada(s) com interesse/salva por você")

    if n_participacao > 0:
        score += min(20, n_participacao * 10)
        motivos.append(
            f"{n_participacao} no seu fluxo de participação/acompanhamento"
        )

    if n_resultado > 0:
        score += min(15, n_resultado * 5)
        motivos.append(f"{n_resultado} com resultado registrado por você")

    if tem_anotacao:
        score += 5
        motivos.append("Há anotação local neste órgão")

    if not motivos:
        motivos.append("Sem sinais além da presença no banco")

    return {
        "prioridade_score": score,
        "motivos_prioridade": motivos,
    }


def _sinais_usuario_por_numero(conn: sqlite3.Connection) -> dict[str, dict[str, int]]:
    """Mapa numero_controle_pncp → contagens de acompanhamento/fluxo do usuário."""
    out: dict[str, dict[str, int]] = {}

    def bucket(num: str) -> dict[str, int]:
        b = out.get(num)
        if not b:
            b = {"interesse_salva": 0, "participacao": 0, "resultado": 0}
            out[num] = b
        return b

    if _table_exists(conn, "oportunidade_acompanhamento"):
        for r in conn.execute(
            """
            SELECT numero_controle_pncp, salva, interesse, decisao
            FROM oportunidade_acompanhamento
            """
        ):
            b = bucket(r["numero_controle_pncp"])
            if int(r["salva"] or 0) or int(r["interesse"] or 0):
                b["interesse_salva"] = 1
            elif (r["decisao"] or "sem_decisao") != "sem_decisao":
                b["interesse_salva"] = 1

    if _table_exists(conn, "oportunidade_fluxo"):
        estados_part = {
            "participacao_registrada",
            "em_acompanhamento",
            "em_preparacao",
            "aguardando_informacoes",
            "em_analise",
        }
        for r in conn.execute(
            """
            SELECT numero_controle_pncp, estado_fluxo, resultado_disputa
            FROM oportunidade_fluxo
            """
        ):
            b = bucket(r["numero_controle_pncp"])
            est = r["estado_fluxo"] or ""
            if est in estados_part or est == "encerrada":
                b["participacao"] = 1
            rd = r["resultado_disputa"] or "nao_informado"
            if rd not in ("", "nao_informado"):
                b["resultado"] = 1
    return out


def list_orgaos(
    conn: sqlite3.Connection,
    *,
    uf: str | None = None,
    q: str | None = None,
    limit: int = 200,
    offset: int = 0,
) -> dict[str, Any]:
    ensure_classificacoes_basicas(conn)
    sql = "SELECT * FROM oportunidades"
    params: list[Any] = []
    if uf:
        sql += " WHERE uf = ?"
        params.append(uf.upper())
    rows = conn.execute(sql, params).fetchall()
    setores_por_opp: dict[str, set[str]] = {}
    for cl in conn.execute("SELECT numero_controle_pncp, setor FROM oportunidade_classificacoes"):
        setores_por_opp.setdefault(cl["numero_controle_pncp"], set()).add(cl["setor"])

    sinais_num = _sinais_usuario_por_numero(conn)
    nome_para_cnpj = _mapa_nome_para_cnpj(rows)
    buckets: dict[str, dict[str, Any]] = {}
    for r in rows:
        chave, cnpj, nome = resolver_orgao_chave(
            r["orgao_razao_social"] or "", r["raw_json"], nome_para_cnpj
        )
        raw = _parse_raw(r["raw_json"])
        mun = _municipio(raw, r["municipio_ibge"])
        b = buckets.get(chave)
        if not b:
            b = {
                "orgao_chave": chave,
                "cnpj": cnpj,
                "nome": nome,
                "ufs": set(),
                "municipios": set(),
                "n_oportunidades": 0,
                "setores": set(),
                "valor_estimado_soma": 0.0,
                "valor_estimado_n": 0,
                "data_min": None,
                "data_max": None,
                "n_abertas": 0,
                "n_interesse_ou_salva": 0,
                "n_participacao": 0,
                "n_resultado": 0,
            }
            buckets[chave] = b
        else:
            # Preferir nome mais longo / com CNPJ já resolvido
            if cnpj and not b["cnpj"]:
                b["cnpj"] = cnpj
            if nome and len(nome) > len(b["nome"] or ""):
                b["nome"] = nome
        b["n_oportunidades"] += 1
        if r["uf"]:
            b["ufs"].add(r["uf"])
        if mun:
            b["municipios"].add(mun)
        if r["valor_total_estimado"] is not None:
            b["valor_estimado_soma"] += float(r["valor_total_estimado"])
            b["valor_estimado_n"] += 1
        dp = r["data_publicacao"]
        if dp:
            if b["data_min"] is None or dp < b["data_min"]:
                b["data_min"] = dp
            if b["data_max"] is None or dp > b["data_max"]:
                b["data_max"] = dp
        b["setores"].update(setores_por_opp.get(r["numero_controle_pncp"], set()))
        if _prazo_ainda_aberto(r["data_encerramento"] if "data_encerramento" in r.keys() else None):
            b["n_abertas"] += 1
        sig = sinais_num.get(r["numero_controle_pncp"])
        if sig:
            b["n_interesse_ou_salva"] += sig["interesse_salva"]
            b["n_participacao"] += sig["participacao"]
            b["n_resultado"] += sig["resultado"]

    items = []
    qn = (q or "").strip().lower()
    for b in buckets.values():
        if qn and qn not in (b["nome"] or "").lower() and qn not in (b["cnpj"] or ""):
            continue
        an = _buscar_anotacao(
            conn, b["orgao_chave"], cnpj=b.get("cnpj"), nome=b.get("nome")
        )
        tem_anotacao = bool(an and (an["anotacoes"] or "").strip())
        valor = (
            round(b["valor_estimado_soma"], 2) if b["valor_estimado_n"] else None
        )
        pri = calcular_prioridade_orgao(
            n_oportunidades=b["n_oportunidades"],
            n_setores=len(b["setores"]),
            valor_estimado_soma=valor,
            data_max_publicacao=b["data_max"],
            n_abertas=b["n_abertas"],
            n_interesse_ou_salva=b["n_interesse_ou_salva"],
            n_participacao=b["n_participacao"],
            n_resultado=b["n_resultado"],
            tem_anotacao=tem_anotacao,
        )
        items.append(
            {
                "orgao_chave": b["orgao_chave"],
                "cnpj": b["cnpj"],
                "nome": b["nome"],
                "ufs": sorted(b["ufs"]),
                "municipios": sorted(b["municipios"])[:8],
                "n_oportunidades": b["n_oportunidades"],
                "setores_observados": sorted(b["setores"]),
                "valor_estimado_soma": valor,
                "periodo_publicacao": {"de": b["data_min"], "ate": b["data_max"]},
                "tem_anotacao": tem_anotacao,
                "prioridade_score": pri["prioridade_score"],
                "motivos_prioridade": pri["motivos_prioridade"],
            }
        )
    items.sort(
        key=lambda x: (
            -int(x["prioridade_score"]),
            -int(x["n_oportunidades"]),
            x["nome"] or "",
        )
    )
    total = len(items)
    page = items[offset : offset + limit]

    return {
        "items": page,
        "total": total,
        "limit": limit,
        "offset": offset,
        "aviso": (
            "Órgãos derivados das oportunidades já coletadas neste computador. "
            "CNPJ é normalizado (só dígitos); a mesma razão social sem CNPJ une-se ao "
            "CNPJ já visto em outra oportunidade. Nomes só parecidos não são unidos. "
            "Prioridade (§12.2) = sinais locais explicáveis (frequência, categorias, "
            "valores/período, seu acompanhamento e resultados) — não é reputação."
        ),
        "limitacoes": [
            "Base: apenas oportunidades presentes no SQLite local.",
            "CNPJ: orgaoEntidade / unidadeOrgao / campos soltos do JSON PNCP, quando existirem.",
            "Sem fusão fuzzy de nomes distintos (ex.: Pref. vs Prefeitura).",
            "Sem dados de participantes/vencedores nesta coleta.",
            "Prioridade não indica boa ou má reputação do órgão.",
        ],
    }


def get_orgao(conn: sqlite3.Connection, orgao_chave: str) -> dict[str, Any] | None:
    ensure_classificacoes_basicas(conn)
    lista = list_orgaos(conn, limit=5000)["items"]
    meta = next((x for x in lista if x["orgao_chave"] == orgao_chave), None)
    if not meta:
        # Aceitar chave antiga nome:… se já houve merge para cnpj:…
        nn = orgao_chave[5:] if orgao_chave.startswith("nome:") else ""
        if nn:
            meta = next(
                (
                    x
                    for x in lista
                    if normalizar_nome_orgao(x.get("nome")) == nn
                    or x["orgao_chave"] == orgao_chave
                ),
                None,
            )
        if not meta:
            return None

    chave_canon = meta["orgao_chave"]
    rows = conn.execute("SELECT * FROM oportunidades").fetchall()
    nome_para_cnpj = _mapa_nome_para_cnpj(rows)

    opps = []
    cats: dict[str, int] = {}
    for r in rows:
        chave, _, _ = resolver_orgao_chave(
            r["orgao_razao_social"] or "", r["raw_json"], nome_para_cnpj
        )
        if chave != chave_canon:
            continue
        opps.append(
            {
                "numero_controle_pncp": r["numero_controle_pncp"],
                "objeto_compra": r["objeto_compra"],
                "uf": r["uf"],
                "situacao": r["situacao"],
                "data_publicacao": r["data_publicacao"],
                "valor_total_estimado": r["valor_total_estimado"],
                "nicho_legado": r["nicho"],
            }
        )
        for cl in conn.execute(
            """
            SELECT setor, categoria FROM oportunidade_classificacoes
            WHERE numero_controle_pncp = ?
            """,
            (r["numero_controle_pncp"],),
        ):
            label = f"{cl['setor']}/{cl['categoria'] or '—'}"
            cats[label] = cats.get(label, 0) + 1

    an = _buscar_anotacao(
        conn, chave_canon, cnpj=meta.get("cnpj"), nome=meta.get("nome")
    )
    return {
        "orgao": meta,
        "categorias_observadas": [
            {"rotulo": k, "quantidade": v} for k, v in sorted(cats.items(), key=lambda x: -x[1])
        ],
        "oportunidades": sorted(
            opps, key=lambda x: x["data_publicacao"] or "", reverse=True
        )[:100],
        "anotacoes": (an["anotacoes"] if an else "") or "",
        "historico_disponivel": {
            "n_registros": len(opps),
            "periodo": meta.get("periodo_publicacao"),
            "fonte": "oportunidades locais PNCP",
        },
        "aviso": (
            "Detalhe montado só com dados locais. Valores são os informados na coleta "
            "(estimados quando houver). Prioridade lista motivos observáveis — "
            "não é ranking de reputação."
        ),
    }


def upsert_anotacao_orgao(
    conn: sqlite3.Connection, orgao_chave: str, anotacoes: str, nome: str = "", cnpj: str | None = None
) -> dict[str, str]:
    agora = _now()
    conn.execute(
        """
        INSERT INTO orgao_anotacoes (orgao_chave, cnpj, nome_exibicao, anotacoes, atualizado_em)
        VALUES (?,?,?,?,?)
        ON CONFLICT(orgao_chave) DO UPDATE SET
          anotacoes=excluded.anotacoes,
          nome_exibicao=COALESCE(NULLIF(excluded.nome_exibicao,''), orgao_anotacoes.nome_exibicao),
          cnpj=COALESCE(excluded.cnpj, orgao_anotacoes.cnpj),
          atualizado_em=excluded.atualizado_em
        """,
        (orgao_chave, cnpj, nome, anotacoes or "", agora),
    )
    conn.commit()
    return {"orgao_chave": orgao_chave, "anotacoes": anotacoes or "", "atualizado_em": agora}


def list_classificacoes_opp(conn: sqlite3.Connection, numero: str) -> list[dict[str, Any]]:
    ensure_classificacoes_basicas(conn)
    rows = conn.execute(
        """
        SELECT * FROM oportunidade_classificacoes
        WHERE numero_controle_pncp = ? ORDER BY id
        """,
        (numero,),
    ).fetchall()
    return [dict(r) for r in rows]


def add_classificacao(
    conn: sqlite3.Connection,
    numero: str,
    *,
    setor: str,
    categoria: str = "",
    subcategoria: str = "",
    origem: str = "usuario",
) -> dict[str, Any]:
    opp = conn.execute(
        "SELECT 1 FROM oportunidades WHERE numero_controle_pncp = ?", (numero,)
    ).fetchone()
    if not opp:
        raise ValueError("Oportunidade não encontrada.")
    setor = (setor or "").strip().lower()
    if not setor:
        raise ValueError("Setor é obrigatório.")
    agora = _now()
    conn.execute(
        """
        INSERT INTO oportunidade_classificacoes (
          numero_controle_pncp, setor, categoria, subcategoria,
          origem, revisado_pelo_usuario, atualizado_em
        ) VALUES (?,?,?,?,?,?,?)
        ON CONFLICT(numero_controle_pncp, setor, categoria, subcategoria) DO UPDATE SET
          origem=excluded.origem,
          revisado_pelo_usuario=1,
          atualizado_em=excluded.atualizado_em
        """,
        (
            numero,
            setor,
            (categoria or "").strip(),
            (subcategoria or "").strip(),
            origem,
            1 if origem == "usuario" else 0,
            agora,
        ),
    )
    conn.commit()
    return list_classificacoes_opp(conn, numero)[-1]


def visao_categorias(conn: sqlite3.Connection) -> dict[str, Any]:
    """Visão por nicho (coluna oportunidades) — clique na UI aplica filtro na lista."""
    from otto_core.niche import NICHOS_LABELS

    ensure_classificacoes_basicas(conn)
    rows = conn.execute(
        """
        SELECT COALESCE(nicho, 'outros') AS setor, COUNT(*) AS c
        FROM oportunidades
        GROUP BY COALESCE(nicho, 'outros')
        ORDER BY c DESC
        """
    ).fetchall()
    return {
        "items": [
            {
                "setor": r["setor"],
                "categoria": NICHOS_LABELS.get(str(r["setor"]), str(r["setor"])),
                "nicho": r["setor"],
                "quantidade": int(r["c"]),
            }
            for r in rows
        ],
        "aviso": (
            "Categorias = nichos do classificador local (regras sobre objeto/órgão). "
            "Clique num setor para filtrar a Lista geral."
        ),
        "limitacoes": [
            "Setor 'outros' é residual (sem regra forte).",
            "Revisão manual (origem=usuario) não é sobrescrita na reclassificação.",
        ],
    }


def visao_regiao(conn: sqlite3.Connection) -> dict[str, Any]:
    rows = conn.execute(
        """
        SELECT uf, COUNT(*) AS c,
               SUM(CASE WHEN valor_total_estimado IS NOT NULL THEN valor_total_estimado ELSE 0 END) AS soma,
               SUM(CASE WHEN valor_total_estimado IS NOT NULL THEN 1 ELSE 0 END) AS n_val,
               MIN(data_publicacao) AS de,
               MAX(data_publicacao) AS ate
        FROM oportunidades
        GROUP BY uf
        ORDER BY c DESC
        """
    ).fetchall()
    return {
        "items": [
            {
                "uf": r["uf"] or "—",
                "quantidade": int(r["c"]),
                "valor_estimado_soma": float(r["soma"]) if r["n_val"] else None,
                "periodo_publicacao": {"de": r["de"], "ate": r["ate"]},
            }
            for r in rows
        ],
        "aviso": "Visão regional só com UFs presentes no banco local.",
        "limitacoes": [
            "Não representa cobertura nacional.",
            "Município detalhado depende do JSON da unidade orgao.",
        ],
    }


def indicadores_explorar(conn: sqlite3.Connection) -> dict[str, Any]:
    total = conn.execute("SELECT COUNT(*) FROM oportunidades").fetchone()[0]
    com_valor = conn.execute(
        "SELECT COUNT(*) FROM oportunidades WHERE valor_total_estimado IS NOT NULL"
    ).fetchone()[0]
    periodo = conn.execute(
        "SELECT MIN(data_publicacao) de, MAX(data_publicacao) ate FROM oportunidades"
    ).fetchone()
    por_setor = visao_categorias(conn)["items"][:10]
    return {
        "base_calculo": "Tabela oportunidades do SQLite local (coleta PNCP já gravada).",
        "periodo": {"de": periodo["de"], "ate": periodo["ate"]},
        "total_oportunidades": int(total),
        "com_valor_estimado": int(com_valor),
        "pct_com_valor_estimado": round(100 * com_valor / total, 1) if total else 0,
        "top_setores": por_setor,
        "limitacoes": [
            "Indicadores descrevem só o recorte coletado (UFs/modalidades/janela da coleta).",
            "Valor estimado ausente não é tratado como zero.",
            "Não há indicador de concorrência: faltam participantes/vencedores na base.",
            "Score TI legado não entra nestes indicadores de exploração.",
        ],
        "aviso": "Sem dados externos em tempo real nesta tela.",
    }


def concorrencia_status(conn: sqlite3.Connection) -> dict[str, Any]:
    """Verifica se existem registros reais de participantes/resultados."""
    # Varre amostra de raw_json em busca de estruturas típicas.
    chaves_encontradas: set[str] = set()
    n = 0
    for r in conn.execute("SELECT raw_json FROM oportunidades"):
        n += 1
        raw = _parse_raw(r["raw_json"])
        for k in raw:
            kl = k.lower()
            if any(
                x in kl
                for x in ("participante", "participantes", "vencedor", "fornecedor", "propostas")
            ):
                if isinstance(raw[k], (list, dict)) and raw[k]:
                    chaves_encontradas.add(k)
    tem = bool(chaves_encontradas)
    return {
        "dados_suficientes": tem,
        "mensagem": (
            "Análises de concorrência disponíveis com base nos registros locais."
            if tem
            else "Dados insuficientes"
        ),
        "detalhe": (
            None
            if tem
            else (
                "A coleta PNCP gravada neste computador traz o cartão da compra "
                "(órgão, objeto, valores, datas), mas não inclui listas de participantes, "
                "propostas ou vencedores. Quantidade de editais NÃO é usada como medida "
                "de concorrência. Ausência de informação ≠ ausência de concorrentes."
            )
        ),
        "integracao_faltante": (
            None
            if tem
            else (
                "Integração PNCP (ou outra fonte) de resultados/participantes por compra — "
                "ex.: endpoint de resultados/homologação com fornecedores — ainda não "
                "implementada nem autorizada neste lote."
            )
        ),
        "oportunidades_inspecionadas": n,
        "chaves_relevantes_encontradas": sorted(chaves_encontradas),
        "limitacoes": [
            "Não estimar probabilidade de vitória.",
            "Não concluir que um nicho está sem concorrentes por falta de dados.",
        ],
    }


# Evita import circular não usado
_ = Oportunidade
