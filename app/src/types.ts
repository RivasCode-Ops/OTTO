export type ScoreDetalhe = {
  valor: number;
  urgencia: number;
  nicho: number;
  recorrencia: number;
  labels: Record<string, string>;
};

export type Oportunidade = {
  numero_controle_pncp: string;
  orgao_razao_social: string;
  uf: string;
  municipio_ibge?: string | null;
  objeto_compra: string;
  modalidade?: string;
  situacao: string;
  data_publicacao?: string | null;
  data_abertura?: string | null;
  data_encerramento?: string | null;
  data_esclarecimento?: string | null;
  data_impugnacao?: string | null;
  valor_total_estimado?: number | null;
  valor_total_homologado?: number | null;
  qualidade_dados?: string;
  nicho: string;
  confianca_classificacao: string;
  score_total: number;
  score_detalhe: ScoreDetalhe;
  link_sistema_origem?: string | null;
  origem_registro?: 'pncp' | 'manual';
  /** Categoria/setor principal (classificação ou nicho) — só na lista. */
  categoria_principal?: string;
  /** Quantidade de documentos anexados localmente. */
  documentos_count?: number;
  raw_json?: {
    unidadeOrgao?: { municipioNome?: string };
  };
};

export type DecisaoUsuario = 'sem_decisao' | 'prosseguir' | 'nao_prosseguir';

export type Acompanhamento = {
  numero_controle_pncp: string;
  salva: boolean;
  interesse: boolean;
  decisao: DecisaoUsuario;
  observacoes: string;
  justificativa: string;
  atualizado_em?: string | null;
};

export type AcompanhamentoUpdate = {
  salva?: boolean;
  interesse?: boolean;
  decisao?: DecisaoUsuario;
  observacoes?: string;
  justificativa?: string;
};

export type FiltroAcompanhamento = 'salvas' | 'interesse' | 'prosseguir' | 'nao_prosseguir' | 'todos';

export type Cobertura = {
  aviso: string;
  fonte: string;
  config_coleta: {
    ufs: string[];
    modalidades_codigos: number[];
    modalidades: string[];
    janela_dias_padrao: number;
  };
  ultima_execucao: {
    iniciado_em?: string | null;
    finalizado_em?: string | null;
    ufs?: string;
    data_inicial?: string;
    data_final?: string;
    total_bruto?: number;
    total_novos?: number;
    total_atualizados?: number;
    erros?: number;
    mensagem?: string;
  } | null;
  banco: {
    total_oportunidades: number;
    ufs_presentes: string[];
    por_nicho: { nicho: string; quantidade: number }[];
  };
  ordenacao: {
    padrao: string;
    campo_publicacao: string;
    campo_prazo: string;
    rotulo_prazo: string;
    sem_prazo: string;
  };
};

export type Kpis = {
  total: number;
  valor_pipeline: number;
  vencendo_7_dias: number;
  top10: Oportunidade[];
};

export type Evento = {
  id: number;
  tipo: string;
  campo: string;
  valor_anterior?: string | null;
  valor_novo?: string | null;
  detectado_em: string;
};

export type EventoRecente = Evento & {
  numero_controle_pncp: string;
  orgao_razao_social: string;
  objeto_compra: string;
  uf: string;
  nicho: string;
};

export type EventosRecentes = {
  total: number;
  days: number;
  items: EventoRecente[];
};

export type AlertaItem = {
  tipo: 'nova' | 'mudanca';
  titulo: string;
  numero_controle_pncp: string;
  orgao_razao_social?: string;
  objeto_compra?: string;
  score_total?: number;
  campo?: string;
  valor_anterior?: string | null;
  valor_novo?: string | null;
};

export type AlertasResposta = {
  desde: string;
  novas_alta_confianca: number;
  mudancas_7d: number;
  vencendo_urgente_3d: number;
  total: number;
  items: AlertaItem[];
};

export type NaturezaCampo = 'coleta' | 'extraido' | 'usuario' | 'nao_confirmado';

export type DocumentoMeta = {
  id: number;
  numero_controle_pncp: string;
  nome_original: string;
  nome_armazenado: string;
  tipo_mime: string;
  origem: string;
  incluido_em?: string | null;
  versao: number;
  documento_anterior_id?: number | null;
  tamanho_bytes: number;
  status_extracao: string;
  aviso_extracao: string;
};

export type AnaliseCampo = {
  id?: number;
  chave: string;
  rotulo: string;
  valor: string;
  natureza: NaturezaCampo;
  documento_id?: number | null;
  pagina?: number | null;
  trecho: string;
  precisa_revisao?: boolean;
  /** '' | 'usuario' — limpeza de revisão só pelo usuário, nunca automática. */
  revisao_origem?: string;
  atualizado_em?: string | null;
};

export type AnaliseFicha = {
  id: number;
  numero_controle_pncp: string;
  status: string;
  atualizado_em?: string | null;
  aviso: string;
  motivo_desatualizacao?: string;
  campos: AnaliseCampo[];
};

export type ChecklistItem = {
  id: number;
  numero_controle_pncp: string;
  titulo: string;
  descricao: string;
  status: 'pendente' | 'em_andamento' | 'concluido' | 'nao_aplicavel' | 'bloqueada';
  requisito_chave: string;
  categoria?: string;
  observacao?: string;
  prazo_conhecido?: string;
  responsavel?: string;
  evidencia_documento_id?: number | null;
  evidencia_pagina?: number | null;
  evidencia_trecho: string;
  atualizado_em?: string | null;
};

export type FormatosDocumentos = {
  aviso: string;
  extensoes: string[];
  limite_bytes: number;
  ocr_disponivel: boolean;
  ia_analise_disponivel: boolean;
};

export type FluxoOportunidade = {
  numero_controle_pncp: string;
  estado_fluxo:
    | 'nao_avaliada'
    | 'salva'
    | 'em_analise'
    | 'aguardando_informacoes'
    | 'em_preparacao'
    | 'participacao_registrada'
    | 'em_acompanhamento'
    | 'encerrada'
    | 'arquivada';
  resultado_disputa: string;
  resultado_contratacao: string;
  resultado_execucao: string;
  resultado_recebimento: string;
  notas_resultado: string;
  tempo_preparacao_horas?: number | null;
  custo_preparacao?: number | null;
  atualizado_em?: string | null;
  aviso?: string;
};

export type CenarioFinanceiro = {
  id: number;
  numero_controle_pncp: string;
  nome: string;
  receita_estimada?: number | null;
  quantidade?: number | null;
  custo_unitario?: number | null;
  frete?: number | null;
  deslocamento?: number | null;
  mao_obra?: number | null;
  despesas_operacionais?: number | null;
  tributos?: number | null;
  outros_custos?: number | null;
  contingencia?: number | null;
  premissas: string;
  escopo_parcial: boolean;
  receita_realizada?: number | null;
  custos_realizados?: number | null;
  prazo_desembolso?: string;
  prazo_recebimento?: string;
  custos_registrados?: number | null;
  saldo_sobre_custos_registrados?: number | null;
  margem_estimada_pct?: number | null;
  saldo_realizado?: number | null;
  necessidade_caixa_estimada?: number | null;
  incompleto: boolean;
  avisos: string[];
  atualizado_em?: string | null;
};
