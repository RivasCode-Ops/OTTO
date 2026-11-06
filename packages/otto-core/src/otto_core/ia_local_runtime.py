"""Runtime de IA local (Ollama em loopback). Sem nuvem, sem fallback externo."""
from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import urlparse

import httpx

from otto_core.config import IA_LOCAL_BASE_URL, IA_LOCAL_MODEL, IA_LOCAL_MODELS_DIR

# Hosts permitidos — nunca serviços externos.
_LOOPBACK = frozenset({"127.0.0.1", "localhost", "::1"})

AVISO_INSTALACAO = (
    "IA local indisponível neste computador. "
    "Instale Ollama e o modelo autorizado (ver docs/IA-LOCAL.md). "
    "O fluxo manual de documentos/ficha continua funcionando."
)


class IaLocalErro(RuntimeError):
    """Falha de runtime local (não disponível, resposta inválida, etc.)."""


def _assert_loopback(base_url: str) -> str:
    u = urlparse(base_url)
    host = (u.hostname or "").lower()
    if host not in _LOOPBACK:
        raise IaLocalErro(
            f"URL de IA recusada (somente loopback permitido): {base_url!r}. "
            "Não há fallback para nuvem."
        )
    if u.scheme not in {"http", "https"}:
        raise IaLocalErro(f"Esquema de URL de IA inválido: {base_url!r}")
    return base_url.rstrip("/")


def status_runtime(
    *,
    base_url: str | None = None,
    model: str | None = None,
    timeout: float = 1.5,
) -> dict[str, Any]:
    """Diagnóstico local — nunca chama host externo."""
    url = _assert_loopback(base_url or IA_LOCAL_BASE_URL)
    modelo = (model or IA_LOCAL_MODEL).strip() or IA_LOCAL_MODEL
    out: dict[str, Any] = {
        "disponivel": False,
        "runtime": "ollama",
        "base_url": url,
        "modelo_configurado": modelo,
        "modelo_presente": False,
        "modelos_locais": [],
        "models_dir_sugerido": str(IA_LOCAL_MODELS_DIR),
        "aviso": AVISO_INSTALACAO,
        "nuvem": False,
        "ocr_autorizado": True,
    }
    try:
        with httpx.Client(timeout=httpx.Timeout(timeout, connect=0.6)) as client:
            r = client.get(f"{url}/api/tags")
            if r.status_code != 200:
                out["aviso"] = (
                    f"Ollama respondeu HTTP {r.status_code} em {url}. "
                    + AVISO_INSTALACAO
                )
                return out
            data = r.json()
    except httpx.HTTPError as e:
        out["aviso"] = f"Não foi possível contatar Ollama em {url}: {e}. " + AVISO_INSTALACAO
        return out
    except IaLocalErro as e:
        out["aviso"] = str(e)
        return out

    nomes: list[str] = []
    for m in data.get("models") or []:
        name = str(m.get("name") or m.get("model") or "")
        if name:
            nomes.append(name)
    out["modelos_locais"] = nomes
    # Aceita nome exato ou prefixo (qwen2.5:3b ↔ qwen2.5:3b-instruct-…)
    presente = any(
        n == modelo or n.startswith(modelo + "-") or n.startswith(modelo + ":") or modelo in n
        for n in nomes
    )
    # Match mais tolerante: tag base antes de sufixos
    base = modelo.split(":")[0]
    if not presente and base:
        presente = any(n.startswith(base) for n in nomes)
    out["modelo_presente"] = presente
    out["disponivel"] = presente
    if presente:
        out["aviso"] = (
            "IA local disponível via Ollama (loopback). "
            "Sugestões exigem revisão humana antes de aplicar. OCR local: ver docs/OCR.md."
        )
    elif nomes:
        out["aviso"] = (
            f"Ollama está no ar, mas o modelo configurado “{modelo}” não foi encontrado. "
            f"Modelos locais: {', '.join(nomes)}. "
            "Autorize o download do modelo (docs/IA-LOCAL.md)."
        )
    return out


def _extrair_json(texto: str) -> dict[str, Any]:
    texto = (texto or "").strip()
    if not texto:
        raise IaLocalErro("Modelo local devolveu resposta vazia.")
    # Remove cercas markdown comuns
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", texto)
    if fence:
        texto = fence.group(1).strip()
    try:
        data = json.loads(texto)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    # Heurística: primeiro objeto {…}
    start = texto.find("{")
    end = texto.rfind("}")
    if start >= 0 and end > start:
        try:
            data = json.loads(texto[start : end + 1])
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError as e:
            raise IaLocalErro(f"JSON inválido do modelo local: {e}") from e
    raise IaLocalErro("Não foi possível interpretar JSON da resposta do modelo local.")


def gerar_json_local(
    *,
    system: str,
    user: str,
    base_url: str | None = None,
    model: str | None = None,
    timeout: float = 900.0,
) -> dict[str, Any]:
    """Chamada única ao Ollama /api/chat — somente loopback."""
    url = _assert_loopback(base_url or IA_LOCAL_BASE_URL)
    modelo = (model or IA_LOCAL_MODEL).strip() or IA_LOCAL_MODEL
    st = status_runtime(base_url=url, model=modelo, timeout=min(5.0, timeout))
    if not st["disponivel"]:
        raise IaLocalErro(st["aviso"])

    payload = {
        "model": modelo if any(modelo == m or m.startswith(modelo) for m in st["modelos_locais"]) else st["modelos_locais"][0],
        "stream": False,
        "format": "json",
        # num_predict limita resposta — evita hang longo em CPU fraca.
        "options": {"temperature": 0.1, "num_predict": 1200},
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    # Prefer exact configured name if present
    for m in st["modelos_locais"]:
        if m == modelo or m.startswith(modelo):
            payload["model"] = m
            break

    try:
        with httpx.Client(timeout=timeout) as client:
            r = client.post(f"{url}/api/chat", json=payload)
            if r.status_code != 200:
                raise IaLocalErro(f"Ollama /api/chat HTTP {r.status_code}: {r.text[:300]}")
            body = r.json()
    except httpx.HTTPError as e:
        raise IaLocalErro(f"Falha ao chamar Ollama local: {e}") from e

    content = ""
    msg = body.get("message") or {}
    if isinstance(msg, dict):
        content = str(msg.get("content") or "")
    if not content:
        content = str(body.get("response") or "")
    return _extrair_json(content)
