"""
Coleta PNCP — orquestração no core (CLI e API).

DECISÃO (2026-11-06): disparo pela UI usa o mesmo caminho que `otto ingest`.
Um job por vez; janela de dias limitada; UF opcional (whitelist). Sem shell externo.
"""
from __future__ import annotations

import re
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from typing import Any, Callable

from otto_core.config import load_yaml
from otto_core.db import get_connection, init_db, upsert_oportunidade
from otto_core.pncp_client import PncpClient

DAYS_MIN = 1
DAYS_MAX = 30
_UF_RE = re.compile(r"^[A-Za-z]{2}$")

_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="otto-ingest")
_lock = threading.Lock()

CollectFn = Callable[..., list[dict[str, Any]]]


class IngestEmAndamentoError(RuntimeError):
    """Já existe coleta com finalizado_em NULL."""


class IngestParamsError(ValueError):
    """days/uf inválidos."""


def _normalizar_params(
    days: int | None,
    uf: str | None,
    cfg: dict[str, Any],
) -> tuple[int, list[str], list[int]]:
    janela = int(cfg.get("janela_dias_padrao", 7))
    d = int(days) if days is not None else janela
    if d < DAYS_MIN or d > DAYS_MAX:
        raise IngestParamsError(f"days deve estar entre {DAYS_MIN} e {DAYS_MAX}.")
    if uf is None or not str(uf).strip():
        ufs = [str(u).upper() for u in list(cfg.get("ufs", ["PI"]))]
    else:
        u = str(uf).strip().upper()
        if not _UF_RE.match(u):
            raise IngestParamsError("uf deve ter 2 letras (ex.: PI).")
        ufs = [u]
    modalidades = [int(m) for m in cfg.get("modalidades", [6])]
    return d, ufs, modalidades


def coleta_em_andamento(conn: sqlite3.Connection) -> dict[str, Any] | None:
    row = conn.execute(
        """
        SELECT * FROM ingest_runs
        WHERE finalizado_em IS NULL
        ORDER BY id DESC
        LIMIT 1
        """
    ).fetchone()
    if not row:
        return None
    return _row_run(row)


def status_coleta(conn: sqlite3.Connection) -> dict[str, Any]:
    cfg = load_yaml("ingest.yaml")
    andamento = coleta_em_andamento(conn)
    last = conn.execute(
        "SELECT * FROM ingest_runs ORDER BY id DESC LIMIT 1"
    ).fetchone()
    return {
        "em_andamento": andamento is not None,
        "run_atual": andamento,
        "ultima_execucao": _row_run(last) if last else None,
        "config": {
            "ufs": list(cfg.get("ufs") or []),
            "modalidades": [int(m) for m in (cfg.get("modalidades") or [])],
            "janela_dias_padrao": int(cfg.get("janela_dias_padrao") or 7),
            "days_min": DAYS_MIN,
            "days_max": DAYS_MAX,
        },
        "aviso": (
            "Coleta PNCP neste computador. Pode demorar (rede + muitas páginas). "
            "Só uma coleta por vez. Preferências de UF/modalidade vêm de config/ingest.yaml "
            "salvo override de UF neste disparo."
        ),
    }


def executar_coleta(
    *,
    days: int | None = None,
    uf: str | None = None,
    collect_fn: CollectFn | None = None,
    conn: sqlite3.Connection | None = None,
) -> dict[str, Any]:
    """
    Execução síncrona (CLI ou worker).
    Se `conn` for passado, o caller fecha; senão abre/fecha aqui.
    """
    cfg = load_yaml("ingest.yaml")
    d, ufs, modalidades = _normalizar_params(days, uf, cfg)
    data_final = date.today()
    data_inicial = data_final - timedelta(days=max(1, d))

    own = conn is None
    if own:
        conn = get_connection()
        init_db(conn)
    assert conn is not None

    if coleta_em_andamento(conn):
        if own:
            conn.close()
        raise IngestEmAndamentoError("Já existe uma coleta em andamento.")

    cur = conn.execute(
        """
        INSERT INTO ingest_runs (iniciado_em, ufs, data_inicial, data_final, mensagem)
        VALUES (datetime('now'), ?, ?, ?, ?)
        """,
        (",".join(ufs), data_inicial.isoformat(), data_final.isoformat(), "em_andamento"),
    )
    run_id = int(cur.lastrowid)
    conn.commit()

    try:
        if collect_fn is not None:
            raw_items = collect_fn(days=d, ufs=ufs, modalidades=modalidades)
        else:
            client = PncpClient(cfg)
            raw_items = client.collect_window(days=d, ufs=ufs, modalidades=modalidades)

        novos = 0
        atualizados = 0
        erros = 0
        for raw in raw_items:
            try:
                is_new, _ = upsert_oportunidade(conn, raw)
                if is_new:
                    novos += 1
                else:
                    atualizados += 1
            except Exception:
                erros += 1

        conn.execute(
            """
            UPDATE ingest_runs SET
              finalizado_em = datetime('now'),
              total_bruto = ?,
              total_normalizado = ?,
              total_novos = ?,
              total_atualizados = ?,
              erros = ?,
              mensagem = ?
            WHERE id = ?
            """,
            (
                len(raw_items),
                novos + atualizados,
                novos,
                atualizados,
                erros,
                "ok",
                run_id,
            ),
        )
        conn.commit()
        out = {
            "id": run_id,
            "status": "ok",
            "total_bruto": len(raw_items),
            "total_novos": novos,
            "total_atualizados": atualizados,
            "erros": erros,
            "ufs": ufs,
            "days": d,
            "data_inicial": data_inicial.isoformat(),
            "data_final": data_final.isoformat(),
        }
    except Exception as e:
        conn.execute(
            """
            UPDATE ingest_runs SET
              finalizado_em = datetime('now'),
              mensagem = ?
            WHERE id = ?
            """,
            (f"erro: {e}"[:500], run_id),
        )
        conn.commit()
        if own:
            conn.close()
        raise
    finally:
        if own:
            try:
                conn.close()
            except Exception:
                pass

    return out


def iniciar_coleta_async(
    *,
    days: int | None = None,
    uf: str | None = None,
) -> dict[str, Any]:
    """Agenda coleta em background (API). Retorna run criado ou conflito."""
    cfg = load_yaml("ingest.yaml")
    d, ufs, _modalidades = _normalizar_params(days, uf, cfg)
    data_final = date.today()
    data_inicial = data_final - timedelta(days=max(1, d))

    with _lock:
        conn = get_connection()
        init_db(conn)
        try:
            if coleta_em_andamento(conn):
                atual = coleta_em_andamento(conn)
                raise IngestEmAndamentoError(
                    f"Coleta em andamento (id={atual and atual.get('id')})."
                )
            cur = conn.execute(
                """
                INSERT INTO ingest_runs (iniciado_em, ufs, data_inicial, data_final, mensagem)
                VALUES (datetime('now'), ?, ?, ?, ?)
                """,
                (
                    ",".join(ufs),
                    data_inicial.isoformat(),
                    data_final.isoformat(),
                    "em_andamento",
                ),
            )
            run_id = int(cur.lastrowid)
            conn.commit()
        finally:
            conn.close()

        def _run() -> None:
            c = get_connection()
            init_db(c)
            try:
                _executar_run_existente(c, run_id, days=d, uf=uf)
            finally:
                c.close()

        _executor.submit(_run)

    return {
        "id": run_id,
        "status": "em_andamento",
        "ufs": ufs,
        "days": d,
        "data_inicial": data_inicial.isoformat(),
        "data_final": data_final.isoformat(),
        "aviso": "Coleta iniciada em segundo plano. Atualize o status até finalizar.",
    }


def _executar_run_existente(
    conn: sqlite3.Connection,
    run_id: int,
    *,
    days: int,
    uf: str | None,
    collect_fn: CollectFn | None = None,
) -> None:
    """Worker: completa um run já inserido com mensagem=em_andamento."""
    cfg = load_yaml("ingest.yaml")
    d, ufs, modalidades = _normalizar_params(days, uf, cfg)
    try:
        if collect_fn is not None:
            raw_items = collect_fn(days=d, ufs=ufs, modalidades=modalidades)
        else:
            client = PncpClient(cfg)
            raw_items = client.collect_window(days=d, ufs=ufs, modalidades=modalidades)

        novos = 0
        atualizados = 0
        erros = 0
        for raw in raw_items:
            try:
                is_new, _ = upsert_oportunidade(conn, raw)
                if is_new:
                    novos += 1
                else:
                    atualizados += 1
            except Exception:
                erros += 1

        conn.execute(
            """
            UPDATE ingest_runs SET
              finalizado_em = datetime('now'),
              total_bruto = ?,
              total_normalizado = ?,
              total_novos = ?,
              total_atualizados = ?,
              erros = ?,
              mensagem = ?
            WHERE id = ?
            """,
            (
                len(raw_items),
                novos + atualizados,
                novos,
                atualizados,
                erros,
                "ok",
                run_id,
            ),
        )
        conn.commit()
    except Exception as e:
        conn.execute(
            """
            UPDATE ingest_runs SET
              finalizado_em = datetime('now'),
              mensagem = ?
            WHERE id = ?
            """,
            (f"erro: {e}"[:500], run_id),
        )
        conn.commit()


def _row_run(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": int(row["id"]),
        "iniciado_em": row["iniciado_em"],
        "finalizado_em": row["finalizado_em"],
        "ufs": row["ufs"],
        "data_inicial": row["data_inicial"],
        "data_final": row["data_final"],
        "total_bruto": row["total_bruto"],
        "total_novos": row["total_novos"],
        "total_atualizados": row["total_atualizados"],
        "erros": row["erros"],
        "mensagem": row["mensagem"],
    }
