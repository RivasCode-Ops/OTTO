from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from otto_core.analise_store import (
    add_checklist_item,
    checklist_from_campo,
    confirmar_revisao_ficha,
    get_ficha,
    list_checklist,
    update_campo,
    update_checklist_item,
)
from otto_core.backup import criar_backup, listar_backups, restaurar_em_copia
from otto_core.config import DATA_DIR, DB_PATH
from otto_core.ingest_store import (
    IngestEmAndamentoError,
    IngestParamsError,
    iniciar_coleta_async,
    status_coleta,
)
from otto_core.download_anexos_store import (
    DownloadAnexosErro,
    baixar_anexos,
    listar_anexos_remotos,
)
from otto_core.financeiro_store import fluxo_caixa_timeline, list_cenarios, upsert_cenario
from otto_core.aprendizado_store import resumo_aprendizado
from otto_core.auditoria_store import listar as listar_auditoria
from otto_core.auditoria_store import registrar as registrar_auditoria
from otto_core.fluxo_store import get_fluxo, listar_resultados, update_fluxo
from otto_core.orientacao_store import list_orientacao, upsert_orientacao
from otto_core.itens_lotes_store import (
    add_item,
    add_lote,
    list_itens_lotes,
    marcar_autoaplicacoes_existentes,
    update_item,
    update_lote,
)
from otto_core.manual_store import (
    contagens_fluxo,
    criar_oportunidade_manual,
    importar_manuais_json,
    listar_por_fluxo,
)
from otto_core.requisito_store import (
    add_requisito,
    checklist_from_requisito,
    gerar_requisitos_da_ficha,
    list_requisitos,
    update_requisito,
)
from otto_core.ia_analise_store import (
    aplicar_sugestao,
    get_job,
    iniciar_analise,
    listar_jobs,
    listar_sugestoes,
    rejeitar_sugestao,
    status_ia,
)
from otto_core.orgaos_store import (
    add_classificacao,
    concorrencia_status,
    ensure_classificacoes_basicas,
    get_orgao,
    indicadores_explorar,
    list_classificacoes_opp,
    list_orgaos,
    upsert_anotacao_orgao,
    visao_categorias,
    visao_regiao,
)
from otto_core.db import (
    ORDENACAO_LISTA,
    atualizar_prazos_manuais,
    contagens_acompanhamento,
    count_recent_eventos,
    get_acompanhamento,
    get_alertas,
    get_cobertura_coleta,
    get_connection,
    get_oportunidade,
    init_db,
    kpis,
    list_acompanhamento,
    list_eventos,
    count_oportunidades,
    list_oportunidades,
    list_recent_eventos,
    upsert_acompanhamento,
)
from otto_core.document_store import (
    DocumentoErro,
    adicionar_documento,
    reprocessar_extracao,
    caminho_arquivo,
    formatos_info,
    get_documento,
    list_documentos,
    list_paginas,
)
from otto_core.models import (
    AcompanhamentoUpdate,
    AnaliseCampoUpdate,
    CenarioFinanceiroUpsert,
    ChecklistItemCreate,
    ChecklistItemUpdate,
    FluxoUpdate,
)

app = FastAPI(title="OTTO API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5194", "http://localhost:5194"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _empty_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    v = value.strip()
    return v if v else None


def _serialize_opp(o) -> dict:
    d = o.model_dump()
    for k in (
        "data_publicacao",
        "data_abertura",
        "data_encerramento",
        "data_esclarecimento",
        "data_impugnacao",
        "coletado_em",
        "atualizado_em",
    ):
        if d.get(k) and isinstance(d[k], datetime):
            d[k] = d[k].isoformat()
    if hasattr(o.score_detalhe, "model_dump"):
        d["score_detalhe"] = o.score_detalhe.model_dump()
    return d


def _serialize_acomp(a) -> dict:
    d = a.model_dump()
    if d.get("atualizado_em") and isinstance(d["atualizado_em"], datetime):
        d["atualizado_em"] = d["atualizado_em"].isoformat()
    return d


@app.on_event("startup")
def startup() -> None:
    conn = get_connection()
    init_db(conn)
    ensure_classificacoes_basicas(conn)
    try:
        marcar_autoaplicacoes_existentes(conn)
    except Exception:
        pass
    conn.close()


@app.get("/health")
def health() -> dict:
    return {"ok": True, "service": "otto-api"}


@app.get("/api/cobertura")
def get_cobertura() -> dict:
    conn = get_connection()
    try:
        return get_cobertura_coleta(conn)
    finally:
        conn.close()


@app.get("/api/kpis")
def get_kpis(
    nicho: str | None = Query(None, description="Vazio = todos os nichos no banco"),
    uf: str | None = Query(None, description="Vazio = todas as UFs no banco"),
) -> dict:
    conn = get_connection()
    try:
        data = kpis(conn, nicho=_empty_to_none(nicho), uf=_empty_to_none(uf))
        return {
            "total": data["total"],
            "valor_pipeline": data["valor_pipeline"],
            "vencendo_7_dias": data["vencendo_7_dias"],
            "top10": [_serialize_opp(o) for o in data["top10"]],
        }
    finally:
        conn.close()


@app.get("/api/oportunidades")
def get_oportunidades(
    nicho: str | None = Query(None, description="Vazio = todos os setores presentes nos dados"),
    uf: str | None = Query(None, description="Vazio = todas as UFs presentes nos dados"),
    ordenacao: str = Query(
        "publicacao",
        description="publicacao (mais recente) | prazo (encerramento da proposta, mais próximo)",
    ),
    limit: int = Query(200, le=500),
    offset: int = Query(0, ge=0),
    incluir_arquivadas: bool = Query(False),
) -> dict:
    ordem = ordenacao if ordenacao in ORDENACAO_LISTA else "publicacao"
    conn = get_connection()
    try:
        n = _empty_to_none(nicho)
        u = _empty_to_none(uf)
        excluir = not incluir_arquivadas
        total = count_oportunidades(conn, nicho=n, uf=u, excluir_arquivadas=excluir)
        items = list_oportunidades(
            conn,
            nicho=n,
            uf=u,
            ordenacao=ordem,
            limit=limit,
            offset=offset,
            excluir_arquivadas=excluir,
        )
        prazo_campo = "data_encerramento"
        return {
            "items": [_serialize_opp(o) for o in items],
            "count": len(items),
            "total": total,
            "limit": limit,
            "offset": offset,
            "ordenacao": ordem,
            "ordenacao_campo": "data_publicacao" if ordem == "publicacao" else prazo_campo,
            "ordenacao_rotulo": (
                "Publicação mais recente"
                if ordem == "publicacao"
                else "Prazo de encerramento da proposta (mais próximo)"
            ),
        }
    finally:
        conn.close()


@app.post("/api/oportunidades/manual")
def post_oportunidade_manual(body: dict) -> dict:
    conn = get_connection()
    try:
        try:
            valor = body.get("valor_total_estimado")
            valor_f = float(valor) if valor is not None and str(valor).strip() != "" else None
            opp = criar_oportunidade_manual(
                conn,
                objeto_compra=str(body.get("objeto_compra") or ""),
                orgao_razao_social=str(body.get("orgao_razao_social") or ""),
                uf=str(body.get("uf") or ""),
                municipio=str(body.get("municipio") or body.get("municipio_ibge") or ""),
                modalidade=str(body.get("modalidade") or ""),
                situacao=str(body.get("situacao") or "Cadastrada manualmente"),
                data_publicacao=body.get("data_publicacao"),
                data_encerramento=body.get("data_encerramento"),
                valor_total_estimado=valor_f,
                link=body.get("link_sistema_origem") or body.get("link"),
                numero_controle=body.get("numero_controle_pncp"),
            )
        except ValueError as e:
            raise HTTPException(400, str(e)) from e
        return {
            "item": _serialize_opp(opp),
            "aviso": "Oportunidade cadastrada manualmente neste computador (origem ≠ PNCP).",
        }
    finally:
        conn.close()


@app.post("/api/oportunidades/manual/import")
async def post_oportunidades_manual_import(request: Request) -> dict:
    try:
        body = await request.json()
    except Exception as e:
        raise HTTPException(400, "JSON inválido") from e
    conn = get_connection()
    try:
        try:
            return importar_manuais_json(conn, body)
        except ValueError as e:
            raise HTTPException(400, str(e)) from e
    finally:
        conn.close()


@app.get("/api/resultados")
def get_resultados(
    limit: int = Query(200, le=500),
    offset: int = Query(0, ge=0),
) -> dict:
    conn = get_connection()
    try:
        data = listar_resultados(conn, limit=limit, offset=offset)
        return {
            "items": [
                {
                    **{k: v for k, v in x.items() if k != "oportunidade"},
                    "oportunidade": _serialize_opp(x["oportunidade"]),
                }
                for x in data["items"]
            ],
            "count": data["count"],
            "aviso": data["aviso"],
        }
    finally:
        conn.close()


@app.get("/api/auditoria")
def get_auditoria(limit: int = Query(100, le=500)) -> dict:
    conn = get_connection()
    try:
        return listar_auditoria(conn, limit=limit)
    finally:
        conn.close()


@app.get("/api/aprendizado")
def get_aprendizado() -> dict:
    """Resumo local do histórico (auditoria + IA + resultados). Não altera o modelo."""
    conn = get_connection()
    try:
        return resumo_aprendizado(conn)
    finally:
        conn.close()


@app.get("/api/fluxo")
def get_vistas_fluxo(
    estado: str = Query(..., description="estado_fluxo"),
    limit: int = Query(200, le=500),
    offset: int = Query(0, ge=0),
) -> dict:
    conn = get_connection()
    try:
        try:
            items = listar_por_fluxo(conn, estado, limit=limit, offset=offset)
        except ValueError as e:
            raise HTTPException(400, str(e)) from e
        return {
            "estado": estado,
            "items": [
                {
                    "oportunidade": _serialize_opp(x["oportunidade"]),
                    "estado_fluxo": x["estado_fluxo"],
                }
                for x in items
            ],
            "count": len(items),
            "contagens": contagens_fluxo(conn),
            "aviso": (
                "Vistas pelo estado do fluxo local. Arquivar retira da lista geral, "
                "sem apagar histórico."
            ),
        }
    finally:
        conn.close()


@app.get("/api/acompanhamento")
def get_lista_acompanhamento(
    filtro: str = Query("todos", description="salvas|interesse|prosseguir|nao_prosseguir|todos"),
    limit: int = Query(200, le=500),
    offset: int = Query(0, ge=0),
) -> dict:
    conn = get_connection()
    try:
        items = list_acompanhamento(conn, filtro=filtro, limit=limit, offset=offset)
        return {
            "filtro": filtro,
            "count": len(items),
            "contagens": contagens_acompanhamento(conn),
            "aviso": (
                "Salvar ou registrar interesse/decisão é só organização local. "
                "Não envia proposta nem participa de licitação."
            ),
            "items": [
                {
                    "oportunidade": _serialize_opp(x["oportunidade"]),
                    "acompanhamento": _serialize_acomp(x["acompanhamento"]),
                }
                for x in items
            ],
        }
    finally:
        conn.close()


@app.get("/api/acompanhamento/contagens")
def get_contagens() -> dict:
    conn = get_connection()
    try:
        return contagens_acompanhamento(conn)
    finally:
        conn.close()


@app.put("/api/oportunidades/{numero:path}/acompanhamento")
def put_acompanhamento(numero: str, body: AcompanhamentoUpdate) -> dict:
    conn = get_connection()
    try:
        try:
            acomp = upsert_acompanhamento(conn, numero, body)
        except ValueError as e:
            if str(e) == "oportunidade_nao_encontrada":
                raise HTTPException(404, "Oportunidade não encontrada") from e
            if str(e) == "decisao_invalida":
                raise HTTPException(400, "Decisão inválida") from e
            raise
        return {
            "acompanhamento": _serialize_acomp(acomp),
            "aviso": (
                "Registro local atualizado. Interesse ≠ participação. "
                "Prosseguir ≠ envio de proposta."
            ),
        }
    finally:
        conn.close()


@app.get("/api/alertas")
def get_alertas_api(
    nicho: str | None = Query("ti_software"),
    uf: str | None = Query(None),
    desde: str | None = Query(None, description="ISO datetime — default últimas 24h"),
    confianca: str = Query("alta"),
    limit: int = Query(10, le=30),
) -> dict:
    conn = get_connection()
    try:
        data = get_alertas(
            conn,
            nicho=_empty_to_none(nicho) or "ti_software",
            uf=_empty_to_none(uf),
            desde=desde,
            confianca=confianca,
            limit=limit,
        )
        for k in ("novas",):
            for item in data.get(k, []):
                for fk in ("data_publicacao", "data_abertura", "data_encerramento", "coletado_em", "atualizado_em"):
                    if item.get(fk) and isinstance(item[fk], datetime):
                        item[fk] = item[fk].isoformat()
        return data
    finally:
        conn.close()


@app.get("/api/eventos/recentes")
def get_eventos_recentes(
    nicho: str | None = Query(None),
    uf: str | None = Query(None),
    days: int = Query(7, ge=1, le=90),
    limit: int = Query(8, le=50),
) -> dict:
    conn = get_connection()
    try:
        n = _empty_to_none(nicho)
        u = _empty_to_none(uf)
        total = count_recent_eventos(conn, nicho=n, uf=u, days=days)
        items = list_recent_eventos(conn, nicho=n, uf=u, days=days, limit=limit)
        return {"total": total, "items": items, "days": days}
    finally:
        conn.close()


def _ser_dt(v) -> str | None:
    if v is None:
        return None
    if isinstance(v, datetime):
        return v.isoformat()
    return str(v)


def _ser_doc(d) -> dict:
    x = d.model_dump()
    x["incluido_em"] = _ser_dt(x.get("incluido_em"))
    return x


def _ser_ficha(f) -> dict:
    x = f.model_dump()
    x["atualizado_em"] = _ser_dt(x.get("atualizado_em"))
    for c in x.get("campos", []):
        c["atualizado_em"] = _ser_dt(c.get("atualizado_em"))
    return x


def _ser_check(i) -> dict:
    x = i.model_dump()
    x["atualizado_em"] = _ser_dt(x.get("atualizado_em"))
    return x


@app.get("/api/documentos/formatos")
def get_formatos_documentos() -> dict:
    return formatos_info()


@app.get("/api/orgaos")
def api_list_orgaos(
    uf: str | None = Query(None),
    q: str | None = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0),
) -> dict:
    conn = get_connection()
    try:
        return list_orgaos(conn, uf=_empty_to_none(uf), q=q, limit=limit, offset=offset)
    finally:
        conn.close()


@app.get("/api/orgaos/{orgao_chave:path}")
def api_get_orgao(orgao_chave: str) -> dict:
    conn = get_connection()
    try:
        data = get_orgao(conn, orgao_chave)
        if not data:
            raise HTTPException(404, "Órgão não encontrado nos dados locais")
        return data
    finally:
        conn.close()


@app.put("/api/orgaos/{orgao_chave:path}/anotacoes")
def api_put_orgao_anotacoes(orgao_chave: str, body: dict) -> dict:
    conn = get_connection()
    try:
        return upsert_anotacao_orgao(
            conn,
            orgao_chave,
            str(body.get("anotacoes") or ""),
            nome=str(body.get("nome") or ""),
            cnpj=body.get("cnpj"),
        )
    finally:
        conn.close()


@app.get("/api/visoes/categorias")
def api_visao_categorias() -> dict:
    conn = get_connection()
    try:
        return visao_categorias(conn)
    finally:
        conn.close()


@app.get("/api/visoes/regiao")
def api_visao_regiao() -> dict:
    conn = get_connection()
    try:
        return visao_regiao(conn)
    finally:
        conn.close()


@app.get("/api/indicadores/explorar")
def api_indicadores() -> dict:
    conn = get_connection()
    try:
        return indicadores_explorar(conn)
    finally:
        conn.close()


@app.get("/api/concorrencia")
def api_concorrencia() -> dict:
    conn = get_connection()
    try:
        return concorrencia_status(conn)
    finally:
        conn.close()


@app.get("/api/oportunidades/{numero:path}/classificacoes")
def api_get_classificacoes(numero: str) -> dict:
    conn = get_connection()
    try:
        if not get_oportunidade(conn, numero):
            raise HTTPException(404, "Oportunidade não encontrada")
        return {
            "items": list_classificacoes_opp(conn, numero),
            "aviso": "Múltiplas classificações permitidas. Não restringe a lista geral a TI.",
        }
    finally:
        conn.close()


@app.post("/api/oportunidades/{numero:path}/classificacoes")
def api_post_classificacao(numero: str, body: dict) -> dict:
    conn = get_connection()
    try:
        try:
            item = add_classificacao(
                conn,
                numero,
                setor=str(body.get("setor") or ""),
                categoria=str(body.get("categoria") or ""),
                subcategoria=str(body.get("subcategoria") or ""),
                origem="usuario",
            )
        except ValueError as e:
            raise HTTPException(400, str(e)) from e
        return {"item": item, "items": list_classificacoes_opp(conn, numero)}
    finally:
        conn.close()


@app.get("/api/oportunidades/{numero:path}/documentos")
def get_documentos(numero: str) -> dict:
    conn = get_connection()
    try:
        if not get_oportunidade(conn, numero):
            raise HTTPException(404, "Oportunidade não encontrada")
        docs = list_documentos(conn, numero)
        return {
            "items": [_ser_doc(d) for d in docs],
            "formatos": formatos_info(),
            "aviso": (
                "Arquivos ficam só neste computador. Não há download automático de URLs "
                "nem execução do conteúdo."
            ),
        }
    finally:
        conn.close()


@app.post("/api/oportunidades/{numero:path}/documentos")
async def post_documento(numero: str, arquivo: UploadFile = File(...)) -> dict:
    raw = await arquivo.read()
    conn = get_connection()
    try:
        if not get_oportunidade(conn, numero):
            raise HTTPException(404, "Oportunidade não encontrada")
        try:
            doc = adicionar_documento(
                conn,
                numero,
                arquivo.filename or "arquivo",
                raw,
                arquivo.content_type,
            )
        except DocumentoErro as e:
            raise HTTPException(400, str(e)) from e
        # Atualiza status da ficha após novo documento.
        ficha = get_ficha(conn, numero)
        return {
            "documento": _ser_doc(doc),
            "ficha_status": ficha.status,
            "aviso": doc.aviso_extracao or "Documento armazenado localmente.",
        }
    finally:
        conn.close()


@app.get("/api/oportunidades/{numero:path}/documentos/{doc_id}/arquivo")
def download_documento(numero: str, doc_id: int) -> FileResponse:
    conn = get_connection()
    try:
        doc = get_documento(conn, doc_id)
        if not doc or doc.numero_controle_pncp != numero:
            raise HTTPException(404, "Documento não encontrado")
        path = caminho_arquivo(doc)
        if not path.is_file():
            raise HTTPException(404, "Arquivo ausente no disco")
        return FileResponse(
            path,
            filename=doc.nome_original,
            media_type=doc.tipo_mime,
        )
    finally:
        conn.close()


@app.get("/api/oportunidades/{numero:path}/documentos/{doc_id}/paginas")
def get_documento_paginas(numero: str, doc_id: int) -> dict:
    conn = get_connection()
    try:
        doc = get_documento(conn, doc_id)
        if not doc or doc.numero_controle_pncp != numero:
            raise HTTPException(404, "Documento não encontrado")
        pags = list_paginas(conn, doc_id)
        return {
            "documento": _ser_doc(doc),
            "paginas": [p.model_dump() for p in pags],
            "aviso": doc.aviso_extracao
            or (
                "Texto extraído localmente. Não equivale a compreensão completa do edital."
            ),
        }
    finally:
        conn.close()


@app.get("/api/oportunidades/{numero:path}/anexos-remotos")
def get_anexos_remotos(numero: str) -> dict:
    """Lista anexos publicados no PNCP para a contratação (sem baixar)."""
    conn = get_connection()
    try:
        if not get_oportunidade(conn, numero):
            raise HTTPException(404, "Oportunidade não encontrada")
        try:
            return listar_anexos_remotos(conn, numero)
        except DownloadAnexosErro as e:
            raise HTTPException(400, str(e)) from e
    finally:
        conn.close()


@app.post("/api/oportunidades/{numero:path}/anexos-remotos/baixar")
def post_anexos_remotos_baixar(numero: str, body: dict = {}) -> dict:  # noqa: B006
    """Baixa anexos PDF/DOCX/TXT do PNCP para o armazenamento local."""
    seqs = body.get("sequenciais")
    sequenciais: list[int] | None = None
    if seqs is not None:
        if not isinstance(seqs, list):
            raise HTTPException(400, "sequenciais deve ser lista de inteiros")
        try:
            sequenciais = [int(x) for x in seqs]
        except (TypeError, ValueError) as e:
            raise HTTPException(400, "sequenciais inválidos") from e
    max_arq = body.get("max_arquivos", 10)
    try:
        max_arquivos = int(max_arq)
    except (TypeError, ValueError) as e:
        raise HTTPException(400, "max_arquivos inválido") from e

    conn = get_connection()
    try:
        if not get_oportunidade(conn, numero):
            raise HTTPException(404, "Oportunidade não encontrada")
        try:
            out = baixar_anexos(
                conn, numero, sequenciais=sequenciais, max_arquivos=max_arquivos
            )
        except DownloadAnexosErro as e:
            raise HTTPException(400, str(e)) from e
        registrar_auditoria(
            conn,
            "anexos_pncp_baixados",
            numero=numero,
            detalhe=f"baixados={len(out.get('baixados') or [])} erros={len(out.get('erros') or [])}",
        )
        return out
    finally:
        conn.close()


@app.post("/api/oportunidades/{numero:path}/documentos/{doc_id}/ocr")
def post_documento_ocr(numero: str, doc_id: int) -> dict:
    """Reprocessa extração (OCR local se PDF sem texto nativo)."""
    from otto_core.ocr_local import status_ocr

    conn = get_connection()
    try:
        doc = get_documento(conn, doc_id)
        if not doc or doc.numero_controle_pncp != numero:
            raise HTTPException(404, "Documento não encontrado")
        try:
            out = reprocessar_extracao(conn, doc_id)
        except DocumentoErro as e:
            raise HTTPException(400, str(e)) from e
        registrar_auditoria(
            conn,
            "documento_ocr_reprocessado",
            numero=numero,
            detalhe=f"doc_id={doc_id} status={out.status_extracao}",
        )
        return {
            "documento": _ser_doc(out),
            "ocr": status_ocr(),
            "aviso": out.aviso_extracao or "Extração reprocessada.",
        }
    finally:
        conn.close()


@app.get("/api/oportunidades/{numero:path}/analise")
def get_analise(numero: str) -> dict:
    conn = get_connection()
    try:
        if not get_oportunidade(conn, numero):
            raise HTTPException(404, "Oportunidade não encontrada")
        ficha = get_ficha(conn, numero)
        fluxo = get_fluxo(conn, numero)
        return {
            "ficha": _ser_ficha(ficha),
            "documentos": [_ser_doc(d) for d in list_documentos(conn, numero)],
            "checklist": [_ser_check(i) for i in list_checklist(conn, numero)],
            "fluxo": fluxo.model_dump()
            | {"atualizado_em": _ser_dt(fluxo.atualizado_em)},
            "cenarios": [
                c.model_dump() | {"atualizado_em": _ser_dt(c.atualizado_em)}
                for c in list_cenarios(conn, numero)
            ],
            "fluxo_caixa": fluxo_caixa_timeline(conn, numero),
            "orientacao": list_orientacao(conn, numero),
            "requisitos": list_requisitos(conn, numero),
            "itens_lotes": list_itens_lotes(conn, numero),
            "ia_disponivel": False,
        }
    finally:
        conn.close()


@app.get("/api/oportunidades/{numero:path}/requisitos")
def get_requisitos(numero: str) -> dict:
    conn = get_connection()
    try:
        if not get_oportunidade(conn, numero):
            raise HTTPException(404, "Oportunidade não encontrada")
        return list_requisitos(conn, numero)
    finally:
        conn.close()


@app.post("/api/oportunidades/{numero:path}/requisitos")
def post_requisito(numero: str, body: dict) -> dict:
    conn = get_connection()
    try:
        if not get_oportunidade(conn, numero):
            raise HTTPException(404, "Oportunidade não encontrada")
        try:
            item = add_requisito(
                conn,
                numero,
                str(body.get("descricao") or ""),
                origem=str(body.get("origem") or "usuario"),
                estado=str(body.get("estado") or "nao_avaliado"),
            )
        except ValueError as e:
            raise HTTPException(400, str(e)) from e
        return {"item": item, **list_requisitos(conn, numero)}
    finally:
        conn.close()


@app.patch("/api/oportunidades/{numero:path}/requisitos/{req_id}")
def patch_requisito(numero: str, req_id: int, body: dict) -> dict:
    conn = get_connection()
    try:
        if not get_oportunidade(conn, numero):
            raise HTTPException(404, "Oportunidade não encontrada")
        try:
            item = update_requisito(
                conn,
                numero,
                req_id,
                estado=body.get("estado"),
                evidencia_documento_id=body.get("evidencia_documento_id"),
                limpar_evidencia_doc=bool(body.get("limpar_evidencia_doc")),
                evidencia_pagina=body.get("evidencia_pagina"),
                limpar_evidencia_pagina=bool(body.get("limpar_evidencia_pagina")),
                evidencia_trecho=body.get("evidencia_trecho"),
                observacao=body.get("observacao"),
                descricao=body.get("descricao"),
                confirmar_revisao_usuario=bool(body.get("confirmar_revisao_usuario")),
            )
        except ValueError as e:
            raise HTTPException(400, str(e)) from e
        return {"item": item, **list_requisitos(conn, numero)}
    finally:
        conn.close()


@app.post("/api/oportunidades/{numero:path}/requisitos/{req_id}/checklist")
def post_checklist_from_requisito(numero: str, req_id: int) -> dict:
    conn = get_connection()
    try:
        if not get_oportunidade(conn, numero):
            raise HTTPException(404, "Oportunidade não encontrada")
        try:
            item = checklist_from_requisito(conn, numero, req_id)
        except ValueError as e:
            raise HTTPException(400, str(e)) from e
        return {"item": _ser_check(item)}
    finally:
        conn.close()


@app.post("/api/oportunidades/{numero:path}/requisitos/gerar-da-ficha")
def post_gerar_requisitos_ficha(numero: str) -> dict:
    conn = get_connection()
    try:
        if not get_oportunidade(conn, numero):
            raise HTTPException(404, "Oportunidade não encontrada")
        try:
            return gerar_requisitos_da_ficha(conn, numero)
        except ValueError as e:
            raise HTTPException(400, str(e)) from e
    finally:
        conn.close()


@app.patch("/api/oportunidades/{numero:path}/prazos-manuais")
def patch_prazos_manuais(numero: str, body: dict) -> dict:
    conn = get_connection()
    try:
        try:
            opp = atualizar_prazos_manuais(
                conn,
                numero,
                data_esclarecimento=body.get("data_esclarecimento"),
                data_impugnacao=body.get("data_impugnacao"),
                limpar_esclarecimento=bool(body.get("limpar_esclarecimento")),
                limpar_impugnacao=bool(body.get("limpar_impugnacao")),
            )
        except ValueError as e:
            raise HTTPException(404 if "nao_encontrada" in str(e) else 400, str(e)) from e
        return {
            "item": _serialize_opp(opp),
            "aviso": "Prazos manuais de esclarecimento/impugnação gravados neste computador.",
        }
    finally:
        conn.close()


@app.get("/api/oportunidades/{numero:path}/itens-lotes")
def get_itens_lotes(numero: str) -> dict:
    conn = get_connection()
    try:
        if not get_oportunidade(conn, numero):
            raise HTTPException(404, "Oportunidade não encontrada")
        return list_itens_lotes(conn, numero)
    finally:
        conn.close()


@app.post("/api/oportunidades/{numero:path}/lotes")
def post_lote(numero: str, body: dict) -> dict:
    conn = get_connection()
    try:
        if not get_oportunidade(conn, numero):
            raise HTTPException(404, "Oportunidade não encontrada")
        try:
            valor = body.get("valor_estimado")
            valor_f = float(valor) if valor is not None and str(valor).strip() != "" else None
            item = add_lote(
                conn,
                numero,
                codigo=str(body.get("codigo") or ""),
                descricao=str(body.get("descricao") or ""),
                valor_estimado=valor_f,
                observacao=str(body.get("observacao") or ""),
                disputa_separada_confirmada=bool(body.get("disputa_separada_confirmada")),
            )
        except ValueError as e:
            raise HTTPException(400, str(e)) from e
        return {"lote": item, **list_itens_lotes(conn, numero)}
    finally:
        conn.close()


@app.patch("/api/oportunidades/{numero:path}/lotes/{lote_id}")
def patch_lote(numero: str, lote_id: int, body: dict) -> dict:
    conn = get_connection()
    try:
        if not get_oportunidade(conn, numero):
            raise HTTPException(404, "Oportunidade não encontrada")
        try:
            valor = body.get("valor_estimado")
            valor_f = (
                float(valor)
                if "valor_estimado" in body and valor is not None and str(valor).strip() != ""
                else None
            )
            item = update_lote(
                conn,
                numero,
                lote_id,
                disputa_separada_confirmada=body.get("disputa_separada_confirmada"),
                descricao=body.get("descricao"),
                codigo=body.get("codigo"),
                valor_estimado=valor_f if "valor_estimado" in body else None,
                observacao=body.get("observacao"),
            )
        except ValueError as e:
            raise HTTPException(400, str(e)) from e
        return {"lote": item, **list_itens_lotes(conn, numero)}
    finally:
        conn.close()


@app.post("/api/oportunidades/{numero:path}/itens")
def post_item(numero: str, body: dict) -> dict:
    conn = get_connection()
    try:
        if not get_oportunidade(conn, numero):
            raise HTTPException(404, "Oportunidade não encontrada")
        try:

            def _f(k: str) -> float | None:
                v = body.get(k)
                if v is None or str(v).strip() == "":
                    return None
                return float(v)

            item = add_item(
                conn,
                numero,
                descricao=str(body.get("descricao") or ""),
                lote_id=int(body["lote_id"]) if body.get("lote_id") not in (None, "") else None,
                codigo=str(body.get("codigo") or ""),
                quantidade=_f("quantidade"),
                unidade=str(body.get("unidade") or ""),
                valor_unitario=_f("valor_unitario"),
                valor_total=_f("valor_total"),
                observacao=str(body.get("observacao") or ""),
                setor=str(body.get("setor") or ""),
                categoria=str(body.get("categoria") or ""),
            )
        except (ValueError, TypeError) as e:
            raise HTTPException(400, str(e)) from e
        return {"item": item, **list_itens_lotes(conn, numero)}
    finally:
        conn.close()


@app.patch("/api/oportunidades/{numero:path}/itens/{item_id}")
def patch_item(numero: str, item_id: int, body: dict) -> dict:
    conn = get_connection()
    try:
        if not get_oportunidade(conn, numero):
            raise HTTPException(404, "Oportunidade não encontrada")
        try:
            item = update_item(
                conn,
                numero,
                item_id,
                setor=body.get("setor"),
                categoria=body.get("categoria"),
                descricao=body.get("descricao"),
                observacao=body.get("observacao"),
            )
        except ValueError as e:
            raise HTTPException(400, str(e)) from e
        return {"item": item, **list_itens_lotes(conn, numero)}
    finally:
        conn.close()


@app.get("/api/oportunidades/{numero:path}/orientacao")
def get_orientacao(numero: str) -> dict:
    conn = get_connection()
    try:
        if not get_oportunidade(conn, numero):
            raise HTTPException(404, "Oportunidade não encontrada")
        return list_orientacao(conn, numero)
    finally:
        conn.close()


@app.put("/api/oportunidades/{numero:path}/orientacao/{pergunta_id}")
def put_orientacao(numero: str, pergunta_id: str, body: dict) -> dict:
    conn = get_connection()
    try:
        if not get_oportunidade(conn, numero):
            raise HTTPException(404, "Oportunidade não encontrada")
        try:
            return upsert_orientacao(
                conn,
                numero,
                pergunta_id,
                str(body.get("resposta") or "nao_respondida"),
                str(body.get("detalhe") or ""),
            )
        except ValueError as e:
            raise HTTPException(400, str(e)) from e
    finally:
        conn.close()


@app.get("/api/configuracoes")
def get_configuracoes() -> dict:
    """Metadados locais de armazenamento e capacidades — sem secrets."""
    cob = None
    conn = get_connection()
    try:
        cob = get_cobertura_coleta(conn)
    finally:
        conn.close()
    ia = status_ia()
    from otto_core.ocr_local import status_ocr

    ocr = status_ocr()
    return {
        "data_dir": str(DATA_DIR.resolve()),
        "db_path": str(DB_PATH.resolve()),
        "documentos_dir": str((DATA_DIR / "documentos").resolve()),
        "backups_dir": str((DATA_DIR / "backups").resolve()),
        "ia_analise": bool(ia.get("disponivel")),
        "ia_local": ia,
        "ocr": bool(ocr.get("autorizado")),
        "ocr_disponivel": bool(ocr.get("disponivel")),
        "ocr_status": ocr,
        "docx": True,
        "download_automatico_anexos": True,
        "perfil_obrigatorio": False,
        "restore_operacional": {
            "disponivel_na_ui": False,
            "procedimento": (
                "Restauração operacional (substituir otto.db) é procedimento restrito "
                "e exige autorização explícita. A UI só permite restauração em pasta isolada "
                "(data/restore-test-*)."
            ),
        },
        "cobertura": cob,
        "aviso": (
            "Configurações locais. Perfil opcional fica neste navegador e não filtra a lista. "
            "IA, OCR, DOCX e download de anexos PNCP: só neste computador / hosts pncp.gov.br. "
            "Sem nuvem de terceiros."
        ),
    }


@app.get("/api/ia-local/status")
def get_ia_local_status() -> dict:
    return status_ia()


@app.get("/api/oportunidades/{numero:path}/ia-analise")
def get_ia_analise(numero: str) -> dict:
    conn = get_connection()
    try:
        if not get_oportunidade(conn, numero):
            raise HTTPException(404, "Oportunidade não encontrada")
        return {
            "status": status_ia(),
            "jobs": listar_jobs(conn, numero),
            "sugestoes_pendentes": listar_sugestoes(conn, numero, apenas_pendentes=True),
            "aviso": (
                "Sugestões de IA local exigem revisão humana antes de aplicar. "
                "Campos com origem usuário são preservados (a IA não sobrescreve). "
                "Para alterar, edite a ficha manualmente. "
                "Fluxo manual permanece disponível se a IA estiver indisponível."
            ),
        }
    finally:
        conn.close()


@app.get("/api/oportunidades/{numero:path}/ia-analise/jobs/{job_id}")
def get_ia_job(numero: str, job_id: int) -> dict:
    conn = get_connection()
    try:
        if not get_oportunidade(conn, numero):
            raise HTTPException(404, "Oportunidade não encontrada")
        job = get_job(conn, numero, job_id)
        if not job:
            raise HTTPException(404, "Job de análise não encontrado")
        return job
    finally:
        conn.close()


@app.post("/api/oportunidades/{numero:path}/ia-analise")
def post_ia_analise(numero: str, body: dict) -> dict:
    conn = get_connection()
    try:
        if not get_oportunidade(conn, numero):
            raise HTTPException(404, "Oportunidade não encontrada")
        raw_ids = body.get("documento_ids") or []
        if not isinstance(raw_ids, list):
            raise HTTPException(400, "documento_ids deve ser uma lista")
        try:
            ids = [int(x) for x in raw_ids]
        except (TypeError, ValueError) as e:
            raise HTTPException(400, "documento_ids inválidos") from e
        try:
            job = iniciar_analise(conn, numero, ids)
        except ValueError as e:
            raise HTTPException(400, str(e)) from e
        return {"job": job, "status": status_ia()}
    finally:
        conn.close()


@app.post("/api/oportunidades/{numero:path}/ia-analise/sugestoes/{sug_id}/aplicar")
def post_aplicar_sugestao(numero: str, sug_id: int, body: dict = {}) -> dict:
    conn = get_connection()
    try:
        if not get_oportunidade(conn, numero):
            raise HTTPException(404, "Oportunidade não encontrada")
        try:
            res = aplicar_sugestao(
                conn,
                numero,
                sug_id,
                forcar_sobrescrita_usuario=bool((body or {}).get("forcar_sobrescrita_usuario")),
            )
        except ValueError as e:
            raise HTTPException(400, str(e)) from e
        registrar_auditoria(
            conn,
            "ia_sugestao_aplicada",
            numero=numero,
            detalhe=f"id={sug_id}; tipo={res.get('tipo')}; destino={res.get('destino', '')}",
        )
        return {
            "resultado": res,
            "sugestoes_pendentes": listar_sugestoes(conn, numero, apenas_pendentes=True),
        }
    finally:
        conn.close()


@app.post("/api/oportunidades/{numero:path}/ia-analise/sugestoes/{sug_id}/rejeitar")
def post_rejeitar_sugestao(numero: str, sug_id: int) -> dict:
    conn = get_connection()
    try:
        if not get_oportunidade(conn, numero):
            raise HTTPException(404, "Oportunidade não encontrada")
        try:
            res = rejeitar_sugestao(conn, numero, sug_id)
        except ValueError as e:
            raise HTTPException(400, str(e)) from e
        registrar_auditoria(
            conn,
            "ia_sugestao_rejeitada",
            numero=numero,
            detalhe=f"id={sug_id}",
        )
        return {
            "resultado": res,
            "sugestoes_pendentes": listar_sugestoes(conn, numero, apenas_pendentes=True),
        }
    finally:
        conn.close()


@app.post("/api/oportunidades/{numero:path}/analise/confirmar-revisao")
def post_confirmar_revisao(numero: str) -> dict:
    conn = get_connection()
    try:
        if not get_oportunidade(conn, numero):
            raise HTTPException(404, "Oportunidade não encontrada")
        ficha = confirmar_revisao_ficha(conn, numero)
        return {"ficha": _ser_ficha(ficha)}
    finally:
        conn.close()


@app.post("/api/oportunidades/{numero:path}/analise/campos/{chave}/checklist")
def post_checklist_from_campo(numero: str, chave: str) -> dict:
    conn = get_connection()
    try:
        try:
            item = checklist_from_campo(conn, numero, chave)
        except ValueError as e:
            raise HTTPException(400, str(e)) from e
        return {"item": _ser_check(item)}
    finally:
        conn.close()


@app.get("/api/oportunidades/{numero:path}/fluxo")
def get_fluxo_api(numero: str) -> dict:
    conn = get_connection()
    try:
        try:
            fluxo = get_fluxo(conn, numero)
        except ValueError as e:
            raise HTTPException(404, str(e)) from e
        return fluxo.model_dump() | {"atualizado_em": _ser_dt(fluxo.atualizado_em)}
    finally:
        conn.close()


@app.put("/api/oportunidades/{numero:path}/fluxo")
def put_fluxo_api(numero: str, body: FluxoUpdate) -> dict:
    conn = get_connection()
    try:
        try:
            fluxo = update_fluxo(conn, numero, body)
        except ValueError as e:
            raise HTTPException(400, str(e)) from e
        return fluxo.model_dump() | {"atualizado_em": _ser_dt(fluxo.atualizado_em)}
    finally:
        conn.close()


@app.get("/api/oportunidades/{numero:path}/financeiro")
def get_financeiro(numero: str) -> dict:
    conn = get_connection()
    try:
        if not get_oportunidade(conn, numero):
            raise HTTPException(404, "Oportunidade não encontrada")
        tl = fluxo_caixa_timeline(conn, numero)
        return {
            "cenarios": [
                c.model_dump() | {"atualizado_em": _ser_dt(c.atualizado_em)}
                for c in list_cenarios(conn, numero)
            ],
            "fluxo_caixa": tl,
            "aviso": (
                "Cenários estimados ≠ resultados realizados. "
                "Estimativa incompleta não é lucro líquido. "
                + tl["aviso"]
            ),
        }
    finally:
        conn.close()


@app.post("/api/oportunidades/{numero:path}/financeiro")
def post_financeiro(numero: str, body: CenarioFinanceiroUpsert) -> dict:
    conn = get_connection()
    try:
        try:
            c = upsert_cenario(conn, numero, body)
        except ValueError as e:
            raise HTTPException(400, str(e)) from e
        return {"cenario": c.model_dump() | {"atualizado_em": _ser_dt(c.atualizado_em)}}
    finally:
        conn.close()


@app.put("/api/oportunidades/{numero:path}/financeiro/{cenario_id}")
def put_financeiro(numero: str, cenario_id: int, body: CenarioFinanceiroUpsert) -> dict:
    conn = get_connection()
    try:
        try:
            c = upsert_cenario(conn, numero, body, cenario_id=cenario_id)
        except ValueError as e:
            raise HTTPException(400, str(e)) from e
        return {"cenario": c.model_dump() | {"atualizado_em": _ser_dt(c.atualizado_em)}}
    finally:
        conn.close()


@app.get("/api/ingest")
def get_ingest_status() -> dict:
    """Status da coleta PNCP (última execução / em andamento)."""
    conn = get_connection()
    try:
        return status_coleta(conn)
    finally:
        conn.close()


@app.post("/api/ingest")
def post_ingest(
    days: int | None = Query(None, ge=1, le=30, description="Janela retroativa em dias"),
    uf: str | None = Query(None, min_length=2, max_length=2, description="UF opcional (ex: PI)"),
) -> dict:
    """Dispara coleta PNCP em segundo plano (mesmo fluxo do CLI otto ingest)."""
    try:
        out = iniciar_coleta_async(days=days, uf=uf)
    except IngestEmAndamentoError as e:
        raise HTTPException(409, str(e)) from e
    except IngestParamsError as e:
        raise HTTPException(400, str(e)) from e
    conn = get_connection()
    try:
        registrar_auditoria(
            conn,
            "ingest_disparado_ui",
            detalhe=f"id={out.get('id')} days={out.get('days')} ufs={','.join(out.get('ufs') or [])}",
        )
        conn.commit()
    finally:
        conn.close()
    return out


@app.get("/api/backup")
def get_backups() -> dict:
    return {"items": listar_backups(), "aviso": "Backups locais em data/backups/."}


@app.post("/api/backup")
def post_backup() -> dict:
    try:
        return criar_backup()
    except FileNotFoundError as e:
        raise HTTPException(404, str(e)) from e


@app.post("/api/backup/restaurar-em-copia")
def post_restaurar_copia(nome: str = Query(..., description="Nome do zip em data/backups")) -> dict:
    from otto_core.backup import BACKUPS_DIR

    path = (BACKUPS_DIR / Path(nome).name).resolve()
    if not str(path).startswith(str(BACKUPS_DIR.resolve())):
        raise HTTPException(400, "Caminho de backup inválido")
    try:
        return restaurar_em_copia(path)
    except (FileNotFoundError, FileExistsError, ValueError) as e:
        raise HTTPException(400, str(e)) from e


@app.put("/api/oportunidades/{numero:path}/analise/campos/{chave}")
def put_analise_campo(numero: str, chave: str, body: AnaliseCampoUpdate) -> dict:
    conn = get_connection()
    try:
        if not get_oportunidade(conn, numero):
            raise HTTPException(404, "Oportunidade não encontrada")
        try:
            campo = update_campo(conn, numero, chave, body)
        except ValueError as e:
            raise HTTPException(400, str(e)) from e
        return {"campo": campo.model_dump() | {"atualizado_em": _ser_dt(campo.atualizado_em)}}
    finally:
        conn.close()


@app.get("/api/oportunidades/{numero:path}/checklist")
def get_checklist(numero: str) -> dict:
    conn = get_connection()
    try:
        if not get_oportunidade(conn, numero):
            raise HTTPException(404, "Oportunidade não encontrada")
        return {
            "items": [_ser_check(i) for i in list_checklist(conn, numero)],
            "aviso": (
                "Checklist local de organização. Não declara habilitação automática "
                "nem envia documentos/propostas."
            ),
        }
    finally:
        conn.close()


@app.post("/api/oportunidades/{numero:path}/checklist")
def post_checklist(numero: str, body: ChecklistItemCreate) -> dict:
    conn = get_connection()
    try:
        try:
            item = add_checklist_item(conn, numero, body)
        except ValueError as e:
            raise HTTPException(400 if "Título" in str(e) else 404, str(e)) from e
        return {"item": _ser_check(item)}
    finally:
        conn.close()


@app.patch("/api/oportunidades/{numero:path}/checklist/{item_id}")
def patch_checklist(numero: str, item_id: int, body: ChecklistItemUpdate) -> dict:
    conn = get_connection()
    try:
        try:
            item = update_checklist_item(conn, numero, item_id, body)
        except ValueError as e:
            raise HTTPException(404, str(e)) from e
        return {"item": _ser_check(item)}
    finally:
        conn.close()


@app.get("/api/oportunidades/{numero:path}")
def get_oportunidade_detail(numero: str) -> dict:
    conn = get_connection()
    try:
        opp = get_oportunidade(conn, numero)
        if not opp:
            raise HTTPException(404, "Oportunidade não encontrada")
        docs = list_documentos(conn, numero)
        ficha = get_ficha(conn, numero)
        return {
            "oportunidade": _serialize_opp(opp),
            "acompanhamento": _serialize_acomp(get_acompanhamento(conn, numero)),
            "eventos": list_eventos(conn, numero),
            "documentos_resumo": {
                "count": len(docs),
                "itens": [_ser_doc(d) for d in docs[:5]],
            },
            "analise_status": ficha.status,
            "aviso_dados": (
                "Dados da coleta PNCP. Documentos locais e ficha revisável não substituem "
                "leitura completa do edital nem análise por IA (ainda não configurada)."
            ),
        }
    finally:
        conn.close()
