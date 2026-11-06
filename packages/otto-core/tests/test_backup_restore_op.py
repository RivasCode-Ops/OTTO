"""Restore operacional — só com confirmação; nunca sem frase canônica."""
from __future__ import annotations

import json
import sqlite3
import zipfile
from pathlib import Path

import pytest

from otto_core.backup import (
    CONFIRMACAO_RESTORE_OPERACIONAL,
    criar_backup,
    restaurar_em_copia,
    restaurar_operacional,
)


def _mk_db(path: Path, n: int = 1) -> None:
    conn = sqlite3.connect(path)
    conn.execute(
        "CREATE TABLE oportunidades (numero_controle_pncp TEXT PRIMARY KEY, objeto_compra TEXT)"
    )
    for i in range(n):
        conn.execute(
            "INSERT INTO oportunidades VALUES (?, ?)",
            (f"N-{i}", f"Objeto {i}"),
        )
    conn.commit()
    conn.close()


def _zip_from_db(zip_path: Path, db: Path, docs: Path | None = None) -> None:
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.write(db, "otto.db")
        if docs and docs.is_dir():
            for f in docs.rglob("*"):
                if f.is_file():
                    zf.write(f, Path("documentos") / f.relative_to(docs))


def test_restaurar_em_copia_nao_toca_operacional(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    data = tmp_path / "data"
    data.mkdir()
    db = data / "otto.db"
    _mk_db(db, 2)
    docs = data / "documentos"
    docs.mkdir()
    (docs / "a.txt").write_text("x", encoding="utf-8")
    backups = data / "backups"
    backups.mkdir()

    monkeypatch.setattr("otto_core.backup.DATA_DIR", data)
    monkeypatch.setattr("otto_core.backup.DB_PATH", db)
    monkeypatch.setattr("otto_core.backup.DOCUMENTOS_DIR", docs)
    monkeypatch.setattr("otto_core.backup.BACKUPS_DIR", backups)

    b = criar_backup()
    zip_path = Path(b["arquivo"])
    out = restaurar_em_copia(zip_path, destino=data / "restore-test-x")
    assert out["oportunidades"] == 2
    assert db.read_bytes()  # operacional intacto
    assert (data / "restore-test-x" / "otto.db").is_file()


def test_restaurar_operacional_exige_confirmacao(tmp_path: Path):
    data = tmp_path / "data"
    data.mkdir()
    db = data / "otto.db"
    _mk_db(db, 1)
    docs = data / "documentos"
    docs.mkdir()
    backups = data / "backups"
    backups.mkdir()
    src_db = tmp_path / "src.db"
    _mk_db(src_db, 5)
    z = backups / "licitar-backup-demo.zip"
    _zip_from_db(z, src_db)

    with pytest.raises(ValueError, match="Confirmação"):
        restaurar_operacional(
            z,
            confirmacao="errado",
            data_dir=data,
            db_path=db,
            documentos_dir=docs,
        )


def test_restaurar_operacional_substitui_com_safety(tmp_path: Path):
    data = tmp_path / "data"
    data.mkdir()
    db = data / "otto.db"
    _mk_db(db, 1)
    docs = data / "documentos"
    docs.mkdir()
    (docs / "old.txt").write_text("old", encoding="utf-8")
    backups = data / "backups"
    backups.mkdir()

    src_db = tmp_path / "src.db"
    _mk_db(src_db, 7)
    src_docs = tmp_path / "src_docs"
    src_docs.mkdir()
    (src_docs / "new.txt").write_text("new", encoding="utf-8")
    z = backups / "licitar-backup-demo.zip"
    _zip_from_db(z, src_db, src_docs)

    out = restaurar_operacional(
        z,
        confirmacao=CONFIRMACAO_RESTORE_OPERACIONAL,
        data_dir=data,
        db_path=db,
        documentos_dir=docs,
    )
    assert out["ok"] is True
    assert out["oportunidades"] == 7
    assert (backups / out["backup_seguranca"]).is_file()
    conn = sqlite3.connect(db)
    assert conn.execute("SELECT COUNT(*) FROM oportunidades").fetchone()[0] == 7
    conn.close()
    assert (docs / "new.txt").read_text(encoding="utf-8") == "new"
    # pasta antiga preservada
    legados = list(data.glob("documentos-pre-restore-*"))
    assert legados
    assert (legados[0] / "old.txt").is_file()
