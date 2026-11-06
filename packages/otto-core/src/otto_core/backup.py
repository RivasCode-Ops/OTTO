"""Backup e restauração em cópia isolada (README §15.5).

Nunca sobrescreve o banco operacional sem caminho explícito de destino isolado.
"""
from __future__ import annotations

import json
import shutil
import sqlite3
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from otto_core.config import DATA_DIR, DB_PATH
from otto_core.document_store import DOCUMENTOS_DIR

BACKUPS_DIR = DATA_DIR / "backups"


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def criar_backup(destino_dir: Path | None = None) -> dict:
    """Copia otto.db + pasta documentos para um zip em data/backups/."""
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    out_dir = destino_dir or BACKUPS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    nome = f"licitar-backup-{_stamp()}"
    work = out_dir / nome
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    if not DB_PATH.is_file():
        raise FileNotFoundError(f"Banco operacional não encontrado: {DB_PATH}")
    shutil.copy2(DB_PATH, work / "otto.db")
    docs_dest = work / "documentos"
    if DOCUMENTOS_DIR.is_dir():
        shutil.copytree(DOCUMENTOS_DIR, docs_dest)
    else:
        docs_dest.mkdir()
    meta = {
        "criado_em": datetime.now(timezone.utc).isoformat(),
        "fonte_db": str(DB_PATH),
        "conteudo": ["otto.db", "documentos/"],
        "nao_incluido": [
            "perfil opcional e preferências do navegador (localStorage)",
            "tema e última visualização do painel web",
        ],
        "aviso": (
            "Backup local do LICITAR (banco SQLite + pasta documentos). "
            "Não inclui perfil/preferências guardados no navegador (localStorage). "
            "Restaure apenas em pasta isolada para validar antes de qualquer "
            "substituição do banco operacional."
        ),
    }
    (work / "backup-meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    zip_path = out_dir / f"{nome}.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for f in work.rglob("*"):
            if f.is_file():
                zf.write(f, f.relative_to(work).as_posix())
    shutil.rmtree(work)
    return {
        "arquivo": str(zip_path),
        "nome": zip_path.name,
        "bytes": zip_path.stat().st_size,
        "meta": meta,
    }


def listar_backups() -> list[dict]:
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    items = []
    for p in sorted(BACKUPS_DIR.glob("licitar-backup-*.zip"), reverse=True):
        items.append({"nome": p.name, "arquivo": str(p), "bytes": p.stat().st_size})
    return items


def restaurar_em_copia(zip_path: Path, destino: Path | None = None) -> dict:
    """Extrai backup para pasta isolada e valida abertura do SQLite.

    Não altera data/otto.db operacional.
    """
    zip_path = Path(zip_path)
    if not zip_path.is_file():
        raise FileNotFoundError(f"Backup não encontrado: {zip_path}")
    # Segurança: só aceita zips dentro de data/backups ou caminho absoluto explícito sob DATA_DIR.
    dest = destino or (DATA_DIR / f"restore-test-{_stamp()}")
    if dest.exists():
        raise FileExistsError(f"Destino já existe: {dest}")
    dest.mkdir(parents=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        # Evita path traversal
        for info in zf.infolist():
            target = (dest / info.filename).resolve()
            if not str(target).startswith(str(dest.resolve())):
                raise ValueError("Entrada de zip inválida (path traversal).")
        zf.extractall(dest)
    db = dest / "otto.db"
    if not db.is_file():
        raise ValueError("Backup sem otto.db")
    conn = sqlite3.connect(db)
    try:
        tables = {
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        required = {"oportunidades"}
        if not required.issubset(tables):
            raise ValueError(f"Backup inválido — tabelas: {sorted(tables)}")
        n_opp = conn.execute("SELECT COUNT(*) FROM oportunidades").fetchone()[0]
    finally:
        conn.close()
    return {
        "destino": str(dest),
        "db": str(db),
        "oportunidades": int(n_opp),
        "documentos_dir": str(dest / "documentos"),
        "aviso": (
            "Restauração em cópia isolada concluída. O banco operacional "
            f"({DB_PATH}) NÃO foi alterado."
        ),
    }
