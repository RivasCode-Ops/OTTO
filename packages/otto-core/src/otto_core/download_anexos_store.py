"""
Download seletivo de anexos do PNCP para o disco local.

DECISÃO (2026-11-06): autorizado. Só HTTPS em hosts pncp.gov.br (whitelist).
PDF/DOCX/TXT até LIMITE_BYTES. ZIP e outros formatos são listados mas não baixados
automaticamente nesta fatia. Sem nuvem de terceiros.
"""
from __future__ import annotations

import json
import re
import sqlite3
from typing import Any
from urllib.parse import urlparse

import httpx

from otto_core.document_store import (
    FORMATOS_SUPORTADOS,
    LIMITE_BYTES,
    adicionar_documento,
    list_documentos,
)
from otto_core.orgaos_store import normalizar_cnpj

PNCP_ARQUIVOS_BASE = "https://pncp.gov.br/api/pncp/v1"
HOSTS_PERMITIDOS = frozenset({"pncp.gov.br", "www.pncp.gov.br"})
MAX_ANEXOS_POR_DISPARO = 15
TIMEOUT_S = 60.0


class DownloadAnexosErro(ValueError):
    """Falha de listagem/download de anexos PNCP."""


def _parse_raw(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        d = json.loads(raw)
        return d if isinstance(d, dict) else {}
    except json.JSONDecodeError:
        return {}


def resolver_ids_compra(conn: sqlite3.Connection, numero: str) -> dict[str, Any]:
    """Extrai cnpj/ano/sequencial do raw PNCP ou do numero_controle_pncp."""
    row = conn.execute(
        "SELECT raw_json, origem_registro FROM oportunidades WHERE numero_controle_pncp = ?",
        (numero,),
    ).fetchone()
    if not row:
        raise DownloadAnexosErro("Oportunidade não encontrada.")

    raw = _parse_raw(row["raw_json"] if "raw_json" in row.keys() else None)
    ent = raw.get("orgaoEntidade") if isinstance(raw.get("orgaoEntidade"), dict) else {}
    cnpj = normalizar_cnpj(str(ent.get("cnpj") or ""))
    ano = raw.get("anoCompra")
    seq = raw.get("sequencialCompra")

    if (not cnpj or ano is None or seq is None) and numero:
        # Formatos comuns: 12345678000190-2024-1 ou com barras
        m = re.match(
            r"^(\d{11,14})[^\d]+(\d{4})[^\d]+(\d+)$",
            re.sub(r"[^\w\-]", "-", numero),
        )
        if m:
            cnpj = cnpj or normalizar_cnpj(m.group(1))
            ano = ano if ano is not None else int(m.group(2))
            seq = seq if seq is not None else int(m.group(3))

    if not cnpj or ano is None or seq is None:
        raise DownloadAnexosErro(
            "Não foi possível identificar CNPJ/ano/sequencial da contratação no PNCP. "
            "Cadastro manual sem raw PNCP não tem anexos remotos listáveis."
        )
    return {
        "cnpj": cnpj,
        "ano": int(ano),
        "sequencial": int(seq),
        "origem_registro": (row["origem_registro"] if "origem_registro" in row.keys() else "")
        or "",
    }


def _url_permitida(url: str) -> bool:
    try:
        p = urlparse(url)
    except Exception:
        return False
    if p.scheme != "https":
        return False
    host = (p.hostname or "").lower()
    if host not in HOSTS_PERMITIDOS:
        return False
    # Bloqueia userinfo / IP literal
    if p.username or p.password:
        return False
    return True


def _ext_de_nome_ou_url(nome: str, url: str, content_type: str | None) -> str | None:
    n = (nome or "").lower()
    for ext in FORMATOS_SUPORTADOS:
        if n.endswith(ext):
            return ext
    path = urlparse(url).path.lower()
    for ext in FORMATOS_SUPORTADOS:
        if path.endswith(ext):
            return ext
    ct = (content_type or "").split(";")[0].strip().lower()
    for ext, mime in FORMATOS_SUPORTADOS.items():
        if ct == mime:
            return ext
    return None


def _nome_arquivo(meta: dict[str, Any], ext: str) -> str:
    titulo = (meta.get("titulo") or meta.get("tipoDocumentoNome") or "anexo-pncp").strip()
    titulo = re.sub(r"[^\w.\-() ]+", "_", titulo, flags=re.UNICODE).strip() or "anexo-pncp"
    seq = meta.get("sequencialDocumento")
    base = f"{titulo}"
    if seq is not None:
        base = f"pncp-{seq}_{titulo}"
    if not base.lower().endswith(ext):
        base = f"{base}{ext}"
    return base[:180]


def listar_anexos_remotos(
    conn: sqlite3.Connection,
    numero: str,
    *,
    http_get: Any | None = None,
) -> dict[str, Any]:
    ids = resolver_ids_compra(conn, numero)
    url = (
        f"{PNCP_ARQUIVOS_BASE}/orgaos/{ids['cnpj']}/compras/"
        f"{ids['ano']}/{ids['sequencial']}/arquivos"
    )
    if not _url_permitida(url):
        raise DownloadAnexosErro("URL de listagem fora da whitelist PNCP.")

    getter = http_get or _http_get_json
    try:
        payload = getter(url)
    except Exception as e:
        raise DownloadAnexosErro(f"Falha ao listar anexos no PNCP: {e}") from e

    # API pode devolver lista direta ou {"documentos": [...]}
    if isinstance(payload, list):
        docs = payload
    elif isinstance(payload, dict):
        docs = payload.get("documentos") or payload.get("data") or payload.get("items") or []
    else:
        docs = []

    locais = {d.nome_original.lower() for d in list_documentos(conn, numero)}
    items: list[dict[str, Any]] = []
    for d in docs:
        if not isinstance(d, dict):
            continue
        seq = d.get("sequencialDocumento")
        titulo = (d.get("titulo") or "").strip()
        tipo = (d.get("tipoDocumentoNome") or "").strip()
        u = (d.get("url") or "").strip()
        ext = _ext_de_nome_ou_url(titulo, u, None)
        baixavel = bool(ext) and _url_permitida(u) if u else False
        nome_sugerido = _nome_arquivo(d, ext or ".bin")
        items.append(
            {
                "sequencial_documento": seq,
                "titulo": titulo or tipo or f"documento-{seq}",
                "tipo": tipo,
                "url": u,
                "url_permitida": _url_permitida(u) if u else False,
                "baixavel": baixavel,
                "extensao": ext,
                "ja_local": nome_sugerido.lower() in locais,
                "nome_sugerido": nome_sugerido if ext else None,
                "motivo_nao_baixavel": (
                    None
                    if baixavel
                    else (
                        "URL fora de pncp.gov.br"
                        if u and not _url_permitida(u)
                        else "Formato não suportado (só PDF/DOCX/TXT nesta fatia; ZIP exige extração manual)"
                        if not ext
                        else "Sem URL"
                    )
                ),
            }
        )

    return {
        "numero_controle_pncp": numero,
        "compra": ids,
        "items": items,
        "aviso": (
            "Lista vinda da API pública PNCP (api/pncp). "
            "Download só de PDF/DOCX/TXT em https://pncp.gov.br. "
            "ZIP e outros tipos aparecem na lista mas não são baixados automaticamente."
        ),
        "download_autorizado": True,
        "hosts_permitidos": sorted(HOSTS_PERMITIDOS),
    }


def baixar_anexos(
    conn: sqlite3.Connection,
    numero: str,
    *,
    sequenciais: list[int] | None = None,
    max_arquivos: int = 10,
    http_get_bytes: Any | None = None,
    http_get_json: Any | None = None,
) -> dict[str, Any]:
    """Baixa anexos baixáveis e grava via adicionar_documento (origem=download_pncp)."""
    max_arquivos = max(1, min(int(max_arquivos), MAX_ANEXOS_POR_DISPARO))
    lista = listar_anexos_remotos(conn, numero, http_get=http_get_json)
    alvo = set(int(s) for s in sequenciais) if sequenciais else None

    candidatos = []
    for it in lista["items"]:
        if not it.get("baixavel"):
            continue
        seq = it.get("sequencial_documento")
        if alvo is not None and seq not in alvo:
            continue
        if it.get("ja_local"):
            continue
        candidatos.append(it)
        if len(candidatos) >= max_arquivos:
            break

    getter = http_get_bytes or _http_get_bytes
    baixados: list[dict[str, Any]] = []
    erros: list[dict[str, Any]] = []
    pulados = [
        it
        for it in lista["items"]
        if (alvo is None or it.get("sequencial_documento") in (alvo or set()))
        and (not it.get("baixavel") or it.get("ja_local"))
    ]

    for it in candidatos:
        url = it["url"]
        nome = it["nome_sugerido"] or "anexo.pdf"
        try:
            if not _url_permitida(url):
                raise DownloadAnexosErro("URL bloqueada pela whitelist.")
            data, ctype = getter(url)
            if len(data) > LIMITE_BYTES:
                raise DownloadAnexosErro(
                    f"Arquivo excede {LIMITE_BYTES // (1024 * 1024)} MB."
                )
            if len(data) == 0:
                raise DownloadAnexosErro("Arquivo vazio.")
            doc = adicionar_documento(
                conn,
                numero,
                nome,
                data,
                ctype,
                origem="download_pncp",
            )
            baixados.append(
                {
                    "sequencial_documento": it.get("sequencial_documento"),
                    "documento_id": doc.id,
                    "nome": doc.nome_original,
                    "status_extracao": doc.status_extracao,
                    "tamanho_bytes": doc.tamanho_bytes,
                }
            )
        except Exception as e:
            erros.append(
                {
                    "sequencial_documento": it.get("sequencial_documento"),
                    "titulo": it.get("titulo"),
                    "erro": str(e)[:300],
                }
            )

    return {
        "numero_controle_pncp": numero,
        "baixados": baixados,
        "erros": erros,
        "pulados": [
            {
                "sequencial_documento": p.get("sequencial_documento"),
                "titulo": p.get("titulo"),
                "motivo": "já local" if p.get("ja_local") else p.get("motivo_nao_baixavel"),
            }
            for p in pulados
        ],
        "aviso": (
            f"{len(baixados)} arquivo(s) gravado(s) localmente (origem download_pncp). "
            "Revise o texto extraído antes de usar na análise/IA."
        ),
    }


def _http_get_json(url: str) -> Any:
    with httpx.Client(
        timeout=TIMEOUT_S,
        follow_redirects=True,
        max_redirects=3,
    ) as client:
        r = client.get(url, headers={"Accept": "application/json"})
        # Revalida host final após redirects
        if not _url_permitida(str(r.url)):
            raise DownloadAnexosErro(f"Redirect para host não permitido: {r.url}")
        r.raise_for_status()
        return r.json()


def _http_get_bytes(url: str) -> tuple[bytes, str | None]:
    with httpx.Client(
        timeout=TIMEOUT_S,
        follow_redirects=True,
        max_redirects=3,
    ) as client:
        r = client.get(url)
        if not _url_permitida(str(r.url)):
            raise DownloadAnexosErro(f"Redirect para host não permitido: {r.url}")
        r.raise_for_status()
        ctype = r.headers.get("content-type")
        content = r.content
        if len(content) > LIMITE_BYTES + 1024:
            raise DownloadAnexosErro("Resposta maior que o limite permitido.")
        return content[:LIMITE_BYTES], ctype
