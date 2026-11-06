"""Validação rápida pós-ingest PI."""
import json
import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parents[1] / "data" / "otto.db"


def main() -> None:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    print("=== INGEST RUNS ===")
    for r in conn.execute("SELECT * FROM ingest_runs ORDER BY id DESC LIMIT 3"):
        print(dict(r))

    print("\n=== TOTAIS ===")
    print("oportunidades:", conn.execute("SELECT COUNT(*) FROM oportunidades").fetchone()[0])
    print("por UF:", [(r[0], r[1]) for r in conn.execute("SELECT uf, COUNT(*) c FROM oportunidades GROUP BY uf")])
    print(
        "por nicho (PI):",
        [
            (r[0], r[1])
            for r in conn.execute(
                "SELECT nicho, COUNT(*) c FROM oportunidades WHERE uf='PI' GROUP BY nicho ORDER BY c DESC"
            )
        ],
    )
    print("eventos:", conn.execute("SELECT COUNT(*) FROM oportunidade_eventos").fetchone()[0])

    print("\n=== UF FORA DE PI ===")
    bad = [
        r[0]
        for r in conn.execute(
            "SELECT DISTINCT uf FROM oportunidades WHERE uf IS NOT NULL AND uf != 'PI'"
        )
    ]
    print(bad if bad else "Nenhum (ok)")
    if bad:
        print("  (nota: dados SP legados no SQLite; painel/API filtram uf=PI)")

    print("\n=== MUNICIPIOS IBGE (top 15, PI) ===")
    for r in conn.execute(
        """
        SELECT municipio_ibge, COUNT(*) c FROM oportunidades
        WHERE uf='PI' GROUP BY municipio_ibge ORDER BY c DESC LIMIT 15
        """
    ):
        nome = r[0] or "(sem ibge)"
        print(f"  {nome}: {r[1]}")

    print("\n=== SCORE TI (distribuicao) ===")
    for r in conn.execute(
        """
        SELECT
          CASE
            WHEN score_total >= 80 THEN '80+'
            WHEN score_total >= 50 THEN '50-79'
            WHEN score_total >= 20 THEN '20-49'
            ELSE '<20'
          END bucket,
          COUNT(*) c
        FROM oportunidades WHERE nicho='ti_software'
        GROUP BY bucket ORDER BY bucket DESC
        """
    ):
        print(f"  {r[0]}: {r[1]}")

    fields = [
        "numero_controle_pncp",
        "orgao_razao_social",
        "municipio_ibge",
        "uf",
        "objeto_compra",
        "valor_total_estimado",
        "data_encerramento",
        "situacao",
        "score_total",
        "nicho",
        "confianca_classificacao",
        "link_sistema_origem",
    ]

    def show(q: str, label: str) -> None:
        print(f"\n--- {label} ---")
        for row in conn.execute(q):
            d = {k: dict(row)[k] for k in fields if k in dict(row).keys()}
            print(json.dumps(d, ensure_ascii=False))

    show(
        "SELECT * FROM oportunidades WHERE nicho='ti_software' AND uf='PI' ORDER BY score_total DESC LIMIT 3",
        "TI ALTO SCORE",
    )
    show(
        "SELECT * FROM oportunidades WHERE nicho='ti_software' AND uf='PI' AND score_total BETWEEN 45 AND 55 ORDER BY score_total LIMIT 2",
        "TI MEDIO SCORE",
    )
    show(
        "SELECT * FROM oportunidades WHERE nicho='ti_software' AND uf='PI' ORDER BY score_total ASC LIMIT 2",
        "TI BAIXO SCORE",
    )

    conn.close()


if __name__ == "__main__":
    main()
