from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class ScoreDetalhe(BaseModel):
    valor: float = 0
    urgencia: float = 0
    nicho: float = 0
    recorrencia: float = 0
    labels: dict[str, str] = Field(default_factory=dict)


class Oportunidade(BaseModel):
    numero_controle_pncp: str
    sequencial_compra: int | None = None
    orgao_razao_social: str = ""
    uf: str = ""
    municipio_ibge: str | None = None
    objeto_compra: str = ""
    modalidade: str = ""
    modalidade_codigo: int | None = None
    situacao: str = ""
    data_publicacao: datetime | None = None
    data_abertura: datetime | None = None
    data_encerramento: datetime | None = None
    data_esclarecimento: datetime | None = None
    data_impugnacao: datetime | None = None
    valor_total_estimado: float | None = None
    valor_total_homologado: float | None = None
    link_sistema_origem: str | None = None
    nicho: str = "outros"
    confianca_classificacao: Literal["alta", "baixa", "nenhuma"] = "nenhuma"
    score_total: float = 0
    score_detalhe: ScoreDetalhe = Field(default_factory=ScoreDetalhe)
    qualidade_dados: Literal["ok", "incompleto", "suspeito"] = "ok"
    status_monitoramento: str = "ativo"
    origem_registro: Literal["pncp", "manual"] = "pncp"
    # Campos de lista (não persistidos como colunas próprias): categoria e docs anexados.
    categoria_principal: str = ""
    documentos_count: int = 0
    raw_json: dict[str, Any] = Field(default_factory=dict)
    coletado_em: datetime | None = None
    atualizado_em: datetime | None = None


class IngestRun(BaseModel):
    id: int | None = None
    iniciado_em: datetime
    finalizado_em: datetime | None = None
    ufs: str = ""
    data_inicial: str = ""
    data_final: str = ""
    total_bruto: int = 0
    total_normalizado: int = 0
    total_novos: int = 0
    total_atualizados: int = 0
    erros: int = 0
    mensagem: str = ""


class OportunidadeEvento(BaseModel):
    id: int | None = None
    numero_controle_pncp: str
    tipo: str
    campo: str
    valor_anterior: str | None = None
    valor_novo: str | None = None
    detectado_em: datetime


DecisaoUsuario = Literal["sem_decisao", "prosseguir", "nao_prosseguir"]


class Acompanhamento(BaseModel):
    """Escolhas locais do usuário — não implica inscrição ou envio de proposta."""

    numero_controle_pncp: str
    salva: bool = False
    interesse: bool = False
    decisao: DecisaoUsuario = "sem_decisao"
    observacoes: str = ""
    justificativa: str = ""
    atualizado_em: datetime | None = None


class AcompanhamentoUpdate(BaseModel):
    salva: bool | None = None
    interesse: bool | None = None
    decisao: DecisaoUsuario | None = None
    observacoes: str | None = None
    justificativa: str | None = None


NaturezaCampo = Literal[
    "coleta",
    "extraido",
    "interpretacao",
    "estimativa",
    "usuario",
    "nao_confirmado",
    "sugerido_ia",  # aplicado a partir de sugestão local; ainda não confirmado pelo usuário
]
StatusExtracao = Literal["pendente", "ok", "sem_texto", "ocr_necessario", "falhou", "nao_aplicavel"]
StatusFicha = Literal[
    "aguardando_documentos",
    "parcial",
    "revisao_humana",
    "desatualizada",
]
StatusChecklist = Literal[
    "pendente",
    "em_andamento",
    "concluido",
    "nao_aplicavel",
    "bloqueada",
]
EstadoFluxo = Literal[
    "nao_avaliada",
    "salva",
    "em_analise",
    "aguardando_informacoes",
    "em_preparacao",
    "participacao_registrada",
    "em_acompanhamento",
    "encerrada",
    "arquivada",
]
# Resultados distintos — não são equivalentes entre si (README §13).
ResultadoEtapa = Literal[
    "nao_informado",
    "nao_aplicavel",
    "pendente",
    "sim",
    "nao",
    "em_andamento",
    "concluido",
]


class DocumentoMeta(BaseModel):
    id: int
    numero_controle_pncp: str
    nome_original: str
    nome_armazenado: str
    tipo_mime: str
    origem: str = "upload_local"
    incluido_em: datetime | None = None
    versao: int = 1
    documento_anterior_id: int | None = None
    tamanho_bytes: int = 0
    status_extracao: StatusExtracao = "pendente"
    aviso_extracao: str = ""


class DocumentoPagina(BaseModel):
    pagina: int
    texto: str = ""


class AnaliseCampo(BaseModel):
    id: int | None = None
    chave: str
    rotulo: str
    valor: str = ""
    natureza: NaturezaCampo
    documento_id: int | None = None
    pagina: int | None = None
    trecho: str = ""
    precisa_revisao: bool = False
    # '' | 'usuario' — nunca 'automatico' para limpar revisão de evidência.
    revisao_origem: str = ""
    atualizado_em: datetime | None = None


class AnaliseFicha(BaseModel):
    id: int
    numero_controle_pncp: str
    status: StatusFicha = "aguardando_documentos"
    atualizado_em: datetime | None = None
    aviso: str = ""
    motivo_desatualizacao: str = ""
    campos: list[AnaliseCampo] = Field(default_factory=list)


class AnaliseCampoUpdate(BaseModel):
    valor: str
    natureza: NaturezaCampo = "usuario"
    documento_id: int | None = None
    pagina: int | None = None
    trecho: str = ""
    limpar_revisao: bool = True


class ChecklistItem(BaseModel):
    id: int
    numero_controle_pncp: str
    titulo: str
    descricao: str = ""
    status: StatusChecklist = "pendente"
    requisito_chave: str = ""
    categoria: str = ""
    observacao: str = ""
    prazo_conhecido: str = ""
    responsavel: str = ""
    evidencia_documento_id: int | None = None
    evidencia_pagina: int | None = None
    evidencia_trecho: str = ""
    atualizado_em: datetime | None = None


class ChecklistItemCreate(BaseModel):
    titulo: str
    descricao: str = ""
    requisito_chave: str = ""
    categoria: str = ""
    observacao: str = ""
    prazo_conhecido: str = ""
    responsavel: str = ""
    evidencia_documento_id: int | None = None
    evidencia_pagina: int | None = None
    evidencia_trecho: str = ""


class ChecklistItemUpdate(BaseModel):
    titulo: str | None = None
    descricao: str | None = None
    status: StatusChecklist | None = None
    requisito_chave: str | None = None
    categoria: str | None = None
    observacao: str | None = None
    prazo_conhecido: str | None = None
    responsavel: str | None = None
    evidencia_documento_id: int | None = None
    evidencia_pagina: int | None = None
    evidencia_trecho: str | None = None


class FluxoOportunidade(BaseModel):
    numero_controle_pncp: str
    estado_fluxo: EstadoFluxo = "nao_avaliada"
    resultado_disputa: ResultadoEtapa = "nao_informado"
    resultado_contratacao: ResultadoEtapa = "nao_informado"
    resultado_execucao: ResultadoEtapa = "nao_informado"
    resultado_recebimento: ResultadoEtapa = "nao_informado"
    notas_resultado: str = ""
    tempo_preparacao_horas: float | None = None
    custo_preparacao: float | None = None
    atualizado_em: datetime | None = None
    aviso: str = (
        "Estados de preparação, participação e resultados são distintos. "
        "Registrar participação não envia proposta a plataformas."
    )


class FluxoUpdate(BaseModel):
    estado_fluxo: EstadoFluxo | None = None
    resultado_disputa: ResultadoEtapa | None = None
    resultado_contratacao: ResultadoEtapa | None = None
    resultado_execucao: ResultadoEtapa | None = None
    resultado_recebimento: ResultadoEtapa | None = None
    notas_resultado: str | None = None
    tempo_preparacao_horas: float | None = None
    custo_preparacao: float | None = None


class CenarioFinanceiro(BaseModel):
    id: int
    numero_controle_pncp: str
    nome: str = "Cenário 1"
    receita_estimada: float | None = None
    quantidade: float | None = None
    custo_unitario: float | None = None
    frete: float | None = None
    deslocamento: float | None = None
    mao_obra: float | None = None
    despesas_operacionais: float | None = None
    tributos: float | None = None
    outros_custos: float | None = None
    contingencia: float | None = None
    premissas: str = ""
    escopo_parcial: bool = False
    receita_realizada: float | None = None
    custos_realizados: float | None = None
    prazo_desembolso: str = ""
    prazo_recebimento: str = ""
    atualizado_em: datetime | None = None
    # Calculados (não persistidos como "lucro")
    custos_registrados: float | None = None
    saldo_sobre_custos_registrados: float | None = None
    margem_estimada_pct: float | None = None
    saldo_realizado: float | None = None
    necessidade_caixa_estimada: float | None = None
    incompleto: bool = True
    avisos: list[str] = Field(default_factory=list)


class CenarioFinanceiroUpsert(BaseModel):
    nome: str = "Cenário 1"
    receita_estimada: float | None = None
    quantidade: float | None = None
    custo_unitario: float | None = None
    frete: float | None = None
    deslocamento: float | None = None
    mao_obra: float | None = None
    despesas_operacionais: float | None = None
    tributos: float | None = None
    outros_custos: float | None = None
    contingencia: float | None = None
    premissas: str = ""
    escopo_parcial: bool = False
    receita_realizada: float | None = None
    custos_realizados: float | None = None
    prazo_desembolso: str = ""
    prazo_recebimento: str = ""
