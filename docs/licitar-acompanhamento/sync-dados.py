"""Gera dados.js a partir de dados.json (espelho para file://).

Uso (na pasta docs/licitar-acompanhamento):
  python sync-dados.py

Fonte canônica: dados.json — edite só o JSON e rode este script.
"""
from __future__ import annotations

import json
from pathlib import Path

DIR = Path(__file__).resolve().parent
SRC = DIR / "dados.json"
OUT = DIR / "dados.js"


def main() -> None:
    data = json.loads(SRC.read_text(encoding="utf-8"))
    payload = json.dumps(data, ensure_ascii=False, indent=2)
    OUT.write_text(
        "// Gerado por sync-dados.py — NÃO editar à mão.\n"
        "// Fonte canônica: dados.json\n"
        f"window.LICITAR_ACOMPANHAMENTO = {payload};\n",
        encoding="utf-8",
    )
    print(f"OK: {OUT.name} atualizado a partir de {SRC.name}")


if __name__ == "__main__":
    main()
