import sqlite3
from pathlib import Path

c = sqlite3.connect(Path(__file__).parents[1] / "data" / "otto.db")
alta = c.execute(
    "SELECT COUNT(*) FROM oportunidades WHERE uf='PI' AND nicho='ti_software' AND confianca_classificacao='alta'"
).fetchone()[0]
baixa = c.execute(
    "SELECT COUNT(*) FROM oportunidades WHERE uf='PI' AND nicho='ti_software' AND confianca_classificacao='baixa'"
).fetchone()[0]
outros = c.execute("SELECT COUNT(*) FROM oportunidades WHERE uf='PI' AND nicho='outros'").fetchone()[0]
print(f"PI alta={alta} baixa={baixa} outros={outros}")
print("\nTop 5 alta:")
for r in c.execute(
    """
    SELECT score_total, orgao_razao_social, substr(objeto_compra,1,90)
    FROM oportunidades WHERE uf='PI' AND confianca_classificacao='alta'
    ORDER BY score_total DESC LIMIT 5
    """
):
    print(f"  {r[0]:.1f} | {r[1][:40]} | {r[2]}")
