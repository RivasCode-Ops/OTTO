"""Backup e restauração (README §15.5 / §15-restore-op).

DECISÃO (2026-11-06): restore operacional autorizado — substitui otto.db + documentos
somente com confirmação explícita; sempre cria backup de segurança antes.
Restauração em cópia isolada permanece disponível sem confirmação especial.
"""
from __future__ import annotations

import json
import shutil
import sqlite3
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from otto_core.config import DATA_DIR, DB_PATH
from otto_core.document_store import DOCUMENTOS_DIR

BACKUPS_DIR = DATA_DIR / "backups"

# Frase exigida no body da API / UI — evita clique acidental.
CONFIRMACAO_RESTORE_OPERACIONAL = "SUBSTITUIR-BANCO-OPERACIONAL"


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
            "Não inclui perfil/preferências guardados no navegador (localStorage)."
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


def _resolver_zip_em_backups(zip_path: Path) -> Path:
    zip_path = Path(zip_path).resolve()
    base = BACKUPS_DIR.resolve()
    if not str(zip_path).startswith(str(base)):
        raise ValueError("Backup fora de data/backups/ — recusado.")
    if not zip_path.is_file() or zip_path.suffix.lower() != ".zip":
        raise FileNotFoundError(f"Backup não encontrado: {zip_path}")
    if ".." in zip_path.name:
        raise ValueError("Nome de backup inválido.")
    return zip_path


def _extrair_e_validar(zip_path: Path, dest: Path) -> dict:
    """Extrai zip em dest e valida otto.db. dest não deve existir."""
    if dest.exists():
        raise FileExistsError(f"Destino já existe: {dest}")
    dest.mkdir(parents=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
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
        if "oportunidades" not in tables:
            raise ValueError(f"Backup inválido — tabelas: {sorted(tables)}")
        n_opp = int(conn.execute("SELECT COUNT(*) FROM oportunidades").fetchone()[0])
    finally:
        conn.close()
    return {
        "db": db,
        "documentos": dest / "documentos",
        "oportunidades": n_opp,
        "tables": sorted(tables),
    }


def restaurar_em_copia(zip_path: Path, destino: Path | None = None) -> dict:
    """Extrai backup para pasta isolada e valida abertura do SQLite.

    Não altera data/otto.db operacional.
    """
    zip_path = Path(zip_path)
    if not zip_path.is_file():
        raise FileNotFoundError(f"Backup não encontrado: {zip_path}")
    dest = destino or (DATA_DIR / f"restore-test-{_stamp()}")
    info = _extrair_e_validar(zip_path, dest)
    return {
        "destino": str(dest),
        "db": str(info["db"]),
        "oportunidades": info["oportunidades"],
        "documentos_dir": str(info["documentos"]),
        "aviso": (
            "Restauração em cópia isolada concluída. O banco operacional "
            f"({DB_PATH}) NÃO foi alterado."
        ),
    }


def _copiar_com_retry(src: Path, dst: Path, tentativas: int = 8) -> None:
    last: Exception | None = None
    for i in range(tentativas):
        try:
            shutil.copy2(src, dst)
            return
        except OSError as e:
            last = e
            time.sleep(0.15 * (i + 1))
    assert last is not None
    raise OSError(
        f"Não foi possível substituir {dst} (arquivo em uso?). "
        f"Feche a API/painel e tente de novo. Detalhe: {last}"
    ) from last


def restaurar_operacional(
    zip_path: Path,
    *,
    confirmacao: str,
    data_dir: Path | None = None,
    db_path: Path | None = None,
    documentos_dir: Path | None = None,
) -> dict:
    """Substitui o banco operacional e a pasta documentos a partir de um zip.

    Exige confirmacao == CONFIRMACAO_RESTORE_OPERACIONAL.
    Cria backup de segurança do estado atual antes de substituir.
    """
    if (confirmacao or "").strip() != CONFIRMACAO_RESTORE_OPERACIONAL:
        raise ValueError(
            "Confirmação inválida. Digite exatamente: "
            f"{CONFIRMACAO_RESTORE_OPERACIONAL}"
        )

    root = Path(data_dir) if data_dir is not None else DATA_DIR
    db_op = Path(db_path) if db_path is not None else DB_PATH
    docs_op = Path(documentos_dir) if documentos_dir is not None else DOCUMENTOS_DIR
    backups = root / "backups"
    backups.mkdir(parents=True, exist_ok=True)

    zip_path = Path(zip_path).resolve()
    # Em testes, zip pode estar sob root/backups customizado
    if data_dir is None:
        zip_path = _resolver_zip_em_backups(zip_path)
    elif not zip_path.is_file():
        raise FileNotFoundError(f"Backup não encontrado: {zip_path}")

    stamp = _stamp()
    work = root / f"_restore-op-work-{stamp}"
    if work.exists():
        shutil.rmtree(work)

    try:
        info = _extrair_e_validar(zip_path, work)

        # Backup de segurança do estado atual (mesmo se db ausente — só docs)
        safety_nome = f"licitar-backup-pre-restore-{stamp}"
        safety_work = backups / safety_nome
        safety_work.mkdir(parents=True)
        if db_op.is_file():
            shutil.copy2(db_op, safety_work / "otto.db")
        else:
            # banco novo: criar vazio mínimo só para o zip ter estrutura
            (safety_work / "otto.db").write_bytes(b"")
        docs_safety = safety_work / "documentos"
        if docs_op.is_dir():
            shutil.copytree(docs_op, docs_safety)
        else:
            docs_safety.mkdir()
        (safety_work / "backup-meta.json").write_text(
            json.dumps(
                {
                    "criado_em": datetime.now(timezone.utc).isoformat(),
                    "motivo": "segurança automática antes de restore operacional",
                    "backup_restaurado": zip_path.name,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        safety_zip = backups / f"{safety_nome}.zip"
        with zipfile.ZipFile(safety_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for f in safety_work.rglob("*"):
                if f.is_file():
                    zf.write(f, f.relative_to(safety_work).as_posix())
        shutil.rmtree(safety_work)

        # Substituir banco
        db_op.parent.mkdir(parents=True, exist_ok=True)
        _copiar_com_retry(info["db"], db_op)

        # Substituir documentos: preservar pasta antiga com rename
        if docs_op.exists():
            legado = root / f"documentos-pre-restore-{stamp}"
            if legado.exists():
                shutil.rmtree(legado)
            docs_op.rename(legado)
        if info["documentos"].is_dir():
            shutil.copytree(info["documentos"], docs_op)
        else:
            docs_op.mkdir(parents=True, exist_ok=True)

        try:
            from otto_core.db import get_connection

            conn = get_connection()
            try:
                from otto_core.auditoria_store import registrar

                registrar(
                    conn,
                    "restore_operacional",
                    None,
                    (
                        f"backup={zip_path.name}; "
                        f"oportunidades={info['oportunidades']}; "
                        f"safety={safety_zip.name}"
                    ),
                )
            finally:
                conn.close()
        except Exception:
            # Auditoria não deve impedir restore já aplicado
            pass

        return {
            "ok": True,
            "backup_restaurado": zip_path.name,
            "backup_seguranca": safety_zip.name,
            "db": str(db_op),
            "documentos_dir": str(docs_op),
            "oportunidades": info["oportunidades"],
            "aviso": (
                "Restauração operacional concluída: banco e pasta documentos "
                f"substituídos a partir de {zip_path.name}. "
                f"Cópia de segurança automática: {safety_zip.name}. "
                "Recarregue o painel. Se a lista parecer antiga, reinicie a API."
            ),
        }
    finally:
        if work.exists():
            shutil.rmtree(work, ignore_errors=True)
