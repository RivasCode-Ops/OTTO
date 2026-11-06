"""
OCR local para PDF só-imagem.

DECISÃO (2026-11-06): autorizado no produto. Somente neste computador
(Tesseract + render pypdfium2). Sem API externa / nuvem.
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any

# Idiomas preferidos (fallback eng se por ausente).
_LANG_PREF = "por+eng"
_LANG_FALLBACK = "eng"

# Caminhos comuns no Windows (instalador UB Mannheim).
_TESSERACT_CANDIDATES = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
)


def ocr_autorizado() -> bool:
    return True


def encontrar_tesseract() -> str | None:
    env = (os.environ.get("OTTO_TESSERACT_CMD") or os.environ.get("TESSERACT_CMD") or "").strip()
    if env and Path(env).is_file():
        return env
    which = shutil.which("tesseract")
    if which:
        return which
    for p in _TESSERACT_CANDIDATES:
        if Path(p).is_file():
            return p
    return None


def status_ocr() -> dict[str, Any]:
    """Estado do motor — independente da IA Ollama."""
    tess = encontrar_tesseract()
    try:
        import pypdfium2  # noqa: F401

        render_ok = True
    except ImportError:
        render_ok = False
    try:
        import pytesseract  # noqa: F401

        wrapper_ok = True
    except ImportError:
        wrapper_ok = False

    disponivel = bool(tess and render_ok and wrapper_ok)
    if not ocr_autorizado():
        aviso = "OCR não autorizado nesta instalação."
    elif disponivel:
        aviso = (
            f"OCR local disponível (Tesseract). Idioma preferido: {_LANG_PREF}. "
            "PDF sem texto selecionável será lido por OCR neste computador."
        )
    else:
        faltando = []
        if not tess:
            faltando.append("binário Tesseract (por)")
        if not render_ok:
            faltando.append("pacote pypdfium2")
        if not wrapper_ok:
            faltando.append("pacote pytesseract")
        aviso = (
            "OCR autorizado, mas o motor local não está completo. Falta: "
            + ", ".join(faltando)
            + ". Ver docs/OCR.md / docs/INSTALACAO.md. "
            "PDF só-imagem fica guardado com status ocr_necessario até instalar."
        )
    return {
        "autorizado": ocr_autorizado(),
        "disponivel": disponivel,
        "motor": "tesseract" if disponivel else None,
        "tesseract_cmd": tess,
        "idioma": _LANG_PREF,
        "render": "pypdfium2" if render_ok else None,
        "nuvem": False,
        "aviso": aviso,
    }


def ocr_pdf_para_paginas(
    path: Path,
    *,
    so_paginas: set[int] | None = None,
    escala: float = 2.0,
) -> list[tuple[int, str]]:
    """
    Renderiza páginas do PDF e aplica Tesseract.
    `so_paginas`: se informado, só essas (1-based); demais retornam "".
    """
    st = status_ocr()
    if not st["disponivel"]:
        raise RuntimeError(st["aviso"])

    import pypdfium2 as pdfium
    import pytesseract
    from PIL import Image

    cmd = st["tesseract_cmd"]
    assert cmd
    pytesseract.pytesseract.tesseract_cmd = cmd

    pdf = pdfium.PdfDocument(str(path))
    n = len(pdf)
    out: list[tuple[int, str]] = []
    lang = _LANG_PREF
    # Detecta se 'por' existe; senão eng.
    try:
        pytesseract.get_languages(config="")
    except Exception:
        pass
    try:
        langs = set(pytesseract.get_languages(config="") or [])
        if "por" not in langs:
            lang = _LANG_FALLBACK if "eng" in langs or not langs else _LANG_FALLBACK
    except Exception:
        lang = _LANG_FALLBACK

    for i in range(n):
        pagina = i + 1
        if so_paginas is not None and pagina not in so_paginas:
            out.append((pagina, ""))
            continue
        page = pdf[i]
        bitmap = page.render(scale=escala)
        pil: Image.Image = bitmap.to_pil()
        if pil.mode not in ("RGB", "L"):
            pil = pil.convert("RGB")
        try:
            texto = pytesseract.image_to_string(pil, lang=lang) or ""
        except pytesseract.TesseractError:
            texto = pytesseract.image_to_string(pil, lang=_LANG_FALLBACK) or ""
        out.append((pagina, texto))
    return out
