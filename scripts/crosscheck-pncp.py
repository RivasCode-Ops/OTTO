"""Cruza amostras OTTO (PI) com resposta bruta do PNCP."""
from __future__ import annotations

import json
import sqlite3
from datetime import date, timedelta
from pathlib import Path

from otto_core.pncp_client import PncpClient

DB = Path(__file__).resolve().parents[1] / "data" / "otto.db"

# Amostras: TI real, falso positivo nicho, registro genérico
SAMPLES = [
    "06553481000149-1-000093/2026",  # PGE - infra TI (alta confiança)
    "06553606000130-1-000085/2026",  # mobiliário (falso positivo TI)
    "06554083000147-1-000007/2026",  # medicamentos (falso positivo TI)
]

FIELDS = [
    "orgao_razao_social",
    "uf",
    "objeto_compra",
    "valor_total_estimado",
    "data_encerramento",
    "situacao",
    "modalidade_codigo",
]


def pncp_index(days: int = 7) -> dict[str, dict]:
    client = PncpClient()
    data_final = date.today()
    data_inicial = data_final - timedelta(days=days)
    idx: dict[str, dict] = {}
    for raw in client.fetch_publicacoes("PI", data_inicial, data_final, 6):
        num = raw.get("numeroControlePNCP") or raw.get("numeroControlePncp")
        if num:
            idx[str(num)] = raw
    return idx


def main() -> None:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    pncp = pncp_index(7)

    print(f"PNCP index PI pregão 7d: {len(pncp)} itens\n")

    for numero in SAMPLES:
        row = conn.execute(
            "SELECT * FROM oportunidades WHERE numero_controle_pncp = ?", (numero,)
        ).fetchone()
        raw = pncp.get(numero)
        print("=" * 60)
        print(numero)
        if not row:
            print("  OTTO: não encontrado")
            continue
        if not raw:
            print("  PNCP: não na janela 7d (pode ter saído da janela)")
        else:
            from otto_core.normalize import normalize_pncp_item

            norm = normalize_pncp_item(raw)
            print("  Campo          | OTTO                    | PNCP norm")
            for f in FIELDS:
                o = row[f]
                p = norm.get(f if f != "modalidade_codigo" else "modalidade_codigo")
                ok = "OK" if str(o or "") == str(p or "") else "DIFF"
                print(f"  {f:16} | {str(o)[:28]:28} | {str(p)[:28]:28} [{ok}]")
        print(
            f"  score={row['score_total']} nicho={row['nicho']} conf={row['confianca_classificacao']}"
        )

    conn.close()


if __name__ == "__main__":
    main()
