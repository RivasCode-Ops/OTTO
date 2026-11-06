"""Documentos locais + extração de texto (OCR local autorizado; sem envio externo)."""
from __future__ import annotations

import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from otto_core.config import DATA_DIR
from otto_core.models import DocumentoMeta, DocumentoPagina, StatusExtracao
from otto_core.ocr_local import ocr_pdf_para_paginas, status_ocr

DOCUMENTOS_DIR = DATA_DIR / "documentos"

# Formatos efetivamente suportados nesta entrega.
# DECISÃO (2026-11-06): DOCX autorizado (texto via python-docx). .doc legado não.
MIME_DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
FORMATOS_SUPORTADOS: dict[str, str] = {
    ".pdf": "application/pdf",
    ".txt": "text/plain",
    ".docx": MIME_DOCX,
}
LIMITE_BYTES = 25 * 1024 * 1024  # 25 MiB
AVISO_FORMATOS = (
    "Formatos aceitos: PDF (texto ou OCR local), DOCX (Word) e TXT. Máximo 25 MB. "
    "PDF só-imagem: Tesseract local — docs/OCR.md. "
    "Arquivo .doc antigo (Word 97–2003) não é suportado. "
    "Anexos do PNCP: baixe pela oportunidade (hosts pncp.gov.br) — docs/DOWNLOAD-ANEXOS.md."
)


def mime_exige_pagina(tipo_mime: str | None) -> bool:
    """PDF exige página na evidência; TXT/DOCX não (sem paginação física confiável)."""
    mime = (tipo_mime or "").lower()
    if mime.startswith("text/"):
        return False
    if "wordprocessingml" in mime or mime == MIME_DOCX:
        return False
    if "pdf" in mime:
        return True
    return True


class DocumentoErro(ValueError):
    """Erro de validação ou processamento de documento."""


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _safe_stem(nome: str) -> str:
    base = Path(nome).name
    base = re.sub(r"[^\w.\-() ]+", "_", base, flags=re.UNICODE).strip() or "arquivo"
    return base[:180]


def _opp_dir(numero: str) -> Path:
    # IDs PNCP contêm '/'; usar pasta segura.
    pasta = re.sub(r"[^\w.\-]+", "_", numero)[:120]
    path = DOCUMENTOS_DIR / pasta
    path.mkdir(parents=True, exist_ok=True)
    return path


def validar_upload(nome_original: str, tamanho: int, content_type: str | None) -> tuple[str, str]:
    if tamanho <= 0:
        raise DocumentoErro("Arquivo vazio não é aceito.")
    if tamanho > LIMITE_BYTES:
        raise DocumentoErro(f"Arquivo excede o limite de {LIMITE_BYTES // (1024 * 1024)} MB.")
    ext = Path(nome_original).suffix.lower()
    if ext not in FORMATOS_SUPORTADOS:
        raise DocumentoErro(
            f"Formato '{ext or 'desconhecido'}' não suportado. {AVISO_FORMATOS}"
        )
    mime = FORMATOS_SUPORTADOS[ext]
    if content_type and content_type.split(";")[0].strip().lower() not in (
        mime,
        "application/octet-stream",
    ):
        # Aceita octet-stream do browser; rejeita mentira óbvia.
        if content_type.split(";")[0].strip().lower() not in FORMATOS_SUPORTADOS.values():
            pass
    return ext, mime


def _row_doc(r: sqlite3.Row) -> DocumentoMeta:
    return DocumentoMeta(
        id=r["id"],
        numero_controle_pncp=r["numero_controle_pncp"],
        nome_original=r["nome_original"],
        nome_armazenado=r["nome_armazenado"],
        tipo_mime=r["tipo_mime"],
        origem=r["origem"],
        incluido_em=datetime.fromisoformat(r["incluido_em"]) if r["incluido_em"] else None,
        versao=r["versao"],
        documento_anterior_id=r["documento_anterior_id"],
        tamanho_bytes=r["tamanho_bytes"],
        status_extracao=r["status_extracao"],  # type: ignore[arg-type]
        aviso_extracao=r["aviso_extracao"] or "",
    )


def list_documentos(conn: sqlite3.Connection, numero: str) -> list[DocumentoMeta]:
    rows = conn.execute(
        """
        SELECT * FROM oportunidade_documentos
        WHERE numero_controle_pncp = ?
        ORDER BY nome_original COLLATE NOCASE, versao DESC, id DESC
        """,
        (numero,),
    ).fetchall()
    return [_row_doc(r) for r in rows]


def get_documento(conn: sqlite3.Connection, doc_id: int) -> DocumentoMeta | None:
    r = conn.execute("SELECT * FROM oportunidade_documentos WHERE id = ?", (doc_id,)).fetchone()
    return _row_doc(r) if r else None


def caminho_arquivo(doc: DocumentoMeta) -> Path:
    return _opp_dir(doc.numero_controle_pncp) / doc.nome_armazenado


def list_paginas(conn: sqlite3.Connection, doc_id: int) -> list[DocumentoPagina]:
    rows = conn.execute(
        "SELECT pagina, texto FROM documento_paginas WHERE documento_id = ? ORDER BY pagina",
        (doc_id,),
    ).fetchall()
    return [DocumentoPagina(pagina=r["pagina"], texto=r["texto"] or "") for r in rows]


def extrair_texto_arquivo(path: Path, mime: str) -> tuple[StatusExtracao, str, list[tuple[int, str]]]:
    """Retorna status, aviso e lista (pagina, texto)."""
    if mime == "text/plain":
        try:
            texto = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            texto = path.read_text(encoding="latin-1")
        if not texto.strip():
            return "sem_texto", "Arquivo TXT sem conteúdo útil.", []
        return "ok", "", [(1, texto)]

    if mime == "application/pdf":
        try:
            from pypdf import PdfReader
        except ImportError as e:
            raise DocumentoErro("Dependência pypdf ausente no ambiente.") from e
        try:
            reader = PdfReader(str(path))
        except Exception as e:  # noqa: BLE001 — arquivo inválido/corrompido
            return "falhou", f"Não foi possível ler o PDF: {e}", []
        paginas: list[tuple[int, str]] = []
        for i, page in enumerate(reader.pages, start=1):
            try:
                t = page.extract_text() or ""
            except Exception:  # noqa: BLE001
                t = ""
            paginas.append((i, t))
        juntos = "".join(t for _, t in paginas).strip()
        if not juntos:
            return _tentar_ocr_pdf(path, paginas_base=paginas, so_vazias=False)
        vazias_idx = {i for i, t in paginas if not (t or "").strip()}
        if vazias_idx:
            ocr_st = status_ocr()
            if ocr_st["disponivel"]:
                try:
                    return _mesclar_ocr_paginas_vazias(path, paginas, vazias_idx)
                except Exception as e:  # noqa: BLE001
                    aviso = (
                        f"{len(vazias_idx)} página(s) sem texto nativo; "
                        f"OCR parcial falhou ({e}). Trechos nessas páginas podem faltar."
                    )
                    return "ok", aviso, paginas
            aviso = (
                f"{len(vazias_idx)} página(s) sem texto extraível. "
                + (
                    "OCR local indisponível — "
                    + (ocr_st.get("aviso") or "instale Tesseract.")
                    if ocr_st["autorizado"]
                    else "OCR não autorizado."
                )
            )
            return "ok", aviso, paginas
        return "ok", "", paginas

    if mime == MIME_DOCX or "wordprocessingml" in (mime or "").lower():
        return _extrair_docx(path)

    return "nao_aplicavel", "Tipo sem extração de texto.", []


def _extrair_docx(path: Path) -> tuple[StatusExtracao, str, list[tuple[int, str]]]:
    try:
        from docx import Document
    except ImportError as e:
        raise DocumentoErro(
            "Dependência python-docx ausente. Rode INSTALAR-OTTO.bat / pip install python-docx."
        ) from e
    try:
        document = Document(str(path))
    except Exception as e:  # noqa: BLE001
        return "falhou", f"Não foi possível ler o DOCX: {e}", []

    blocos: list[str] = []
    for p in document.paragraphs:
        t = (p.text or "").strip()
        if t:
            blocos.append(t)
    for table in document.tables:
        for row in table.rows:
            cells = [(c.text or "").strip() for c in row.cells]
            line = " | ".join(c for c in cells if c)
            if line:
                blocos.append(line)
    texto = "\n".join(blocos).strip()
    if not texto:
        return (
            "sem_texto",
            "DOCX sem parágrafos/tabelas com texto útil (pode ser só imagens — OCR de DOCX não coberto).",
            [],
        )
    aviso = (
        "Texto extraído do DOCX (parágrafos e tabelas). "
        "Sem numeração de página física — na evidência a página é opcional."
    )
    return "ok", aviso, [(1, texto)]


def _tentar_ocr_pdf(
    path: Path,
    *,
    paginas_base: list[tuple[int, str]],
    so_vazias: bool,
) -> tuple[StatusExtracao, str, list[tuple[int, str]]]:
    ocr_st = status_ocr()
    if not ocr_st["autorizado"]:
        return (
            "ocr_necessario",
            "Nenhum texto nativo no PDF. OCR não autorizado nesta instalação.",
            paginas_base,
        )
    if not ocr_st["disponivel"]:
        return (
            "ocr_necessario",
            "Nenhum texto nativo neste PDF (provável digitalização). "
            + (ocr_st.get("aviso") or "Instale o motor OCR local — docs/OCR.md."),
            paginas_base,
        )
    try:
        if so_vazias:
            vazias = {i for i, t in paginas_base if not (t or "").strip()}
            return _mesclar_ocr_paginas_vazias(path, paginas_base, vazias)
        ocr_pages = ocr_pdf_para_paginas(path)
        texto = "".join(t for _, t in ocr_pages).strip()
        if not texto:
            return (
                "sem_texto",
                "OCR local rodou, mas não encontrou texto útil nas páginas.",
                ocr_pages,
            )
        return "ok", "Texto obtido por OCR local (Tesseract) neste computador.", ocr_pages
    except Exception as e:  # noqa: BLE001
        return (
            "falhou",
            f"OCR local falhou: {e}",
            paginas_base,
        )


def _mesclar_ocr_paginas_vazias(
    path: Path,
    paginas: list[tuple[int, str]],
    vazias: set[int],
) -> tuple[StatusExtracao, str, list[tuple[int, str]]]:
    ocr_map = dict(ocr_pdf_para_paginas(path, so_paginas=vazias))
    merged: list[tuple[int, str]] = []
    for i, t in paginas:
        if i in vazias:
            merged.append((i, ocr_map.get(i, "") or ""))
        else:
            merged.append((i, t))
    ainda = sum(1 for i, t in merged if i in vazias and not (t or "").strip())
    aviso = (
        f"OCR local aplicado em {len(vazias)} página(s) sem texto nativo."
        + (f" {ainda} ainda sem texto após OCR." if ainda else "")
    )
    return "ok", aviso, merged


def reprocessar_extracao(conn: sqlite3.Connection, doc_id: int) -> DocumentoMeta:
    """Refaz extração (útil após instalar Tesseract em docs ocr_necessario)."""
    doc = get_documento(conn, doc_id)
    if not doc:
        raise DocumentoErro("Documento não encontrado.")
    path = caminho_arquivo(doc)
    if not path.is_file():
        raise DocumentoErro("Arquivo do documento não encontrado no disco.")
    status, aviso, paginas = extrair_texto_arquivo(path, doc.tipo_mime)
    conn.execute("DELETE FROM documento_paginas WHERE documento_id = ?", (doc_id,))
    conn.execute(
        "UPDATE oportunidade_documentos SET status_extracao = ?, aviso_extracao = ? WHERE id = ?",
        (status, aviso, doc_id),
    )
    for pagina, texto in paginas:
        conn.execute(
            "INSERT INTO documento_paginas (documento_id, pagina, texto) VALUES (?,?,?)",
            (doc_id, pagina, texto),
        )
    conn.commit()
    out = get_documento(conn, doc_id)
    assert out is not None
    return out


def _proxima_versao(conn: sqlite3.Connection, numero: str, nome_original: str) -> tuple[int, int | None]:
    r = conn.execute(
        """
        SELECT id, versao FROM oportunidade_documentos
        WHERE numero_controle_pncp = ? AND lower(nome_original) = lower(?)
        ORDER BY versao DESC, id DESC LIMIT 1
        """,
        (numero, nome_original),
    ).fetchone()
    if not r:
        return 1, None
    return int(r["versao"]) + 1, int(r["id"])


def adicionar_documento(
    conn: sqlite3.Connection,
    numero: str,
    nome_original: str,
    dados: bytes,
    content_type: str | None = None,
    *,
    origem: str = "upload_local",
) -> DocumentoMeta:
    opp = conn.execute(
        "SELECT 1 FROM oportunidades WHERE numero_controle_pncp = ?", (numero,)
    ).fetchone()
    if not opp:
        raise DocumentoErro("Oportunidade não encontrada.")

    _ext, mime = validar_upload(nome_original, len(dados), content_type)
    versao, anterior_id = _proxima_versao(conn, numero, Path(nome_original).name)
    safe = _safe_stem(nome_original)
    incluido = _now()
    # Nome no disco inclui id provisório via timestamp+versão para não colidir.
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    nome_arm = f"v{versao}_{stamp}_{safe}"
    origem_ok = (origem or "upload_local").strip() or "upload_local"
    if origem_ok not in {"upload_local", "download_pncp"}:
        origem_ok = "upload_local"

    pasta = _opp_dir(numero)
    destino = pasta / nome_arm
    destino.write_bytes(dados)

    cur = conn.execute(
        """
        INSERT INTO oportunidade_documentos (
          numero_controle_pncp, nome_original, nome_armazenado, tipo_mime, origem,
          incluido_em, versao, documento_anterior_id, tamanho_bytes,
          status_extracao, aviso_extracao
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            numero,
            Path(nome_original).name,
            nome_arm,
            mime,
            origem_ok,
            incluido,
            versao,
            anterior_id,
            len(dados),
            "pendente",
            "",
        ),
    )
    doc_id = int(cur.lastrowid)
    status, aviso, paginas = extrair_texto_arquivo(destino, mime)
    conn.execute(
        "UPDATE oportunidade_documentos SET status_extracao = ?, aviso_extracao = ? WHERE id = ?",
        (status, aviso, doc_id),
    )
    for pagina, texto in paginas:
        conn.execute(
            "INSERT INTO documento_paginas (documento_id, pagina, texto) VALUES (?,?,?)",
            (doc_id, pagina, texto),
        )
    conn.commit()
    # Nova versão (ou documento adicional após análise): marcar revisão (README §8.5).
    precisa_sinalizar = versao > 1 or anterior_id is not None
    if not precisa_sinalizar:
        outros = conn.execute(
            """
            SELECT COUNT(*) AS c FROM oportunidade_documentos
            WHERE numero_controle_pncp = ? AND id != ?
            """,
            (numero, doc_id),
        ).fetchone()
        precisa_sinalizar = bool(outros and int(outros["c"]) > 0)
    if precisa_sinalizar:
        from otto_core.analise_store import ensure_ficha, marcar_ficha_desatualizada

        ensure_ficha(conn, numero)
        motivo = (
            f"Nova versão do documento “{Path(nome_original).name}” (v{versao}). "
            if versao > 1 or anterior_id is not None
            else f"Novo documento “{Path(nome_original).name}” incluído. "
        )
        antigos: list[int] = []
        if anterior_id is not None:
            antigos.append(int(anterior_id))
            # Cadeia de versões anteriores (preserva evidências apontando para ids antigos).
            cur_id: int | None = int(anterior_id)
            seen: set[int] = set()
            while cur_id is not None and cur_id not in seen:
                seen.add(cur_id)
                prev = conn.execute(
                    "SELECT documento_anterior_id FROM oportunidade_documentos WHERE id = ?",
                    (cur_id,),
                ).fetchone()
                if not prev or prev["documento_anterior_id"] is None:
                    break
                cur_id = int(prev["documento_anterior_id"])
                antigos.append(cur_id)
        marcar_ficha_desatualizada(
            conn,
            numero,
            motivo
            + "Revise a ficha e os requisitos; evidências na versão antiga foram preservadas "
            "(não atualizadas automaticamente).",
            documento_ids_antigos=antigos,
        )
    doc = get_documento(conn, doc_id)
    assert doc is not None
    return doc


def formatos_info() -> dict:
    from otto_core.ia_local_runtime import status_runtime

    ia = status_runtime()
    ocr = status_ocr()
    return {
        "aviso": AVISO_FORMATOS,
        "extensoes": sorted(FORMATOS_SUPORTADOS.keys()),
        "mimes": sorted(set(FORMATOS_SUPORTADOS.values())),
        "limite_bytes": LIMITE_BYTES,
        "ocr_autorizado": bool(ocr.get("autorizado")),
        "ocr_disponivel": bool(ocr.get("disponivel")),
        "ocr": ocr,
        "docx": True,
        "download_url_automatico": True,
        "download_hosts": ["pncp.gov.br"],
        "ia_analise_disponivel": bool(ia.get("disponivel")),
        "ia_local": {
            "runtime": ia.get("runtime"),
            "modelo": ia.get("modelo_configurado"),
            "aviso": ia.get("aviso"),
            "nuvem": False,
        },
    }
