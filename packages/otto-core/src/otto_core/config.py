from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
CONFIG_DIR = ROOT / "config"
DATA_DIR = Path(os.environ.get("OTTO_DATA_DIR", ROOT / "data"))
DB_PATH = Path(os.environ.get("OTTO_DB_PATH", DATA_DIR / "otto.db"))

# IA local — apenas loopback. Sem fallback em nuvem.
# DECISÃO (2026-11-04): ver docs/IA-LOCAL.md
IA_LOCAL_BASE_URL = os.environ.get("OTTO_IA_LOCAL_URL", "http://127.0.0.1:11434").rstrip("/")
IA_LOCAL_MODEL = os.environ.get("OTTO_IA_LOCAL_MODEL", "qwen2.5:3b")
IA_LOCAL_MODELS_DIR = Path(
    os.environ.get("OTTO_IA_LOCAL_MODELS_DIR", str(DATA_DIR / "ia-models"))
)


def load_yaml(name: str) -> dict:
    import yaml

    path = CONFIG_DIR / name
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}
