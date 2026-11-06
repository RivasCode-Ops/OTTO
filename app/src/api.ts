import type {
  Acompanhamento,
  AcompanhamentoUpdate,
  AlertasResposta,
  Cobertura,
  EventosRecentes,
  FiltroAcompanhamento,
  Kpis,
  Oportunidade,
  Evento,
} from './types';

const base = '';

export type ModoLista = 'geral' | 'ti';
export type OrdenacaoLista = 'publicacao' | 'prazo';

export type ListaOportunidadesMeta = {
  items: Oportunidade[];
  total: number;
  ordenacao: OrdenacaoLista;
  ordenacao_campo: string;
  ordenacao_rotulo: string;
};

/** Extrai `detail` de respostas FastAPI (string ou lista de validações). */
export async function apiErrorMessage(r: Response, fallback: string): Promise<string> {
  const raw = await r.text();
  if (!raw) return fallback;
  try {
    const j = JSON.parse(raw) as { detail?: unknown };
    if (typeof j.detail === 'string' && j.detail.trim()) return j.detail;
    if (Array.isArray(j.detail)) {
      const msgs = j.detail
        .map((d) => {
          if (typeof d === 'string') return d;
          if (d && typeof d === 'object' && 'msg' in d) return String((d as { msg: unknown }).msg);
          return JSON.stringify(d);
        })
        .filter(Boolean);
      if (msgs.length) return msgs.join('; ');
    }
    if (j.detail != null) return String(j.detail);
  } catch {
    /* corpo não-JSON */
  }
  return raw.length > 400 ? `${raw.slice(0, 400)}…` : raw;
}

async function ensureOk(r: Response, fallback: string): Promise<void> {
  if (!r.ok) throw new Error(await apiErrorMessage(r, fallback));
}

function paramsModo(modo: ModoLista): URLSearchParams {
  const q = new URLSearchParams();
  if (modo === 'ti') {
    q.set('nicho', 'ti_software');
  }
  return q;
}

export async function fetchCobertura(signal?: AbortSignal): Promise<Cobertura> {
  const r = await fetch(`${base}/api/cobertura`, { signal });
  await ensureOk(r, 'Falha ao carregar cobertura da coleta');
  return r.json() as Promise<Cobertura>;
}

export async function fetchKpis(modo: ModoLista = 'geral', signal?: AbortSignal): Promise<Kpis> {
  const q = paramsModo(modo);
  const r = await fetch(`${base}/api/kpis?${q}`, { signal });
  await ensureOk(r, 'Falha ao carregar KPIs');
  return r.json() as Promise<Kpis>;
}

const PAGE_SIZE = 500;

export async function fetchOportunidades(
  modo: ModoLista = 'geral',
  ordenacao: OrdenacaoLista = 'publicacao',
  signal?: AbortSignal,
): Promise<ListaOportunidadesMeta> {
  const items: Oportunidade[] = [];
  let offset = 0;
  let total = 0;
  let ordenacaoOut: OrdenacaoLista = ordenacao;
  let ordenacaoCampo =
    ordenacao === 'prazo' ? 'data_encerramento' : 'data_publicacao';
  let ordenacaoRotulo =
    ordenacao === 'prazo'
      ? 'Prazo de encerramento da proposta (mais próximo)'
      : 'Publicação mais recente';

  for (;;) {
    const q = paramsModo(modo);
    q.set('ordenacao', ordenacao);
    q.set('limit', String(PAGE_SIZE));
    q.set('offset', String(offset));
    const r = await fetch(`${base}/api/oportunidades?${q}`, { signal });
    await ensureOk(r, 'Falha ao carregar oportunidades');
    const data = (await r.json()) as {
      items: Oportunidade[];
      total?: number;
      count?: number;
      ordenacao?: OrdenacaoLista;
      ordenacao_campo?: string;
      ordenacao_rotulo?: string;
    };
    const page = data.items || [];
    total = typeof data.total === 'number' ? data.total : offset + page.length;
    ordenacaoOut = data.ordenacao ?? ordenacaoOut;
    ordenacaoCampo = data.ordenacao_campo ?? ordenacaoCampo;
    ordenacaoRotulo = data.ordenacao_rotulo ?? ordenacaoRotulo;
    items.push(...page);
    if (page.length < PAGE_SIZE || items.length >= total) break;
    offset += PAGE_SIZE;
  }

  return {
    items,
    total,
    ordenacao: ordenacaoOut,
    ordenacao_campo: ordenacaoCampo,
    ordenacao_rotulo: ordenacaoRotulo,
  };
}

export async function fetchEventosRecentes(
  modo: ModoLista = 'geral',
  signal?: AbortSignal,
): Promise<EventosRecentes> {
  const q = paramsModo(modo);
  q.set('days', '7');
  q.set('limit', '8');
  const r = await fetch(`${base}/api/eventos/recentes?${q}`, { signal });
  await ensureOk(r, 'Falha ao carregar eventos');
  return r.json() as Promise<EventosRecentes>;
}

export async function fetchAlertas(desde?: string, signal?: AbortSignal): Promise<AlertasResposta> {
  const q = new URLSearchParams({ nicho: 'ti_software', confianca: 'alta' });
  if (desde) q.set('desde', desde);
  const r = await fetch(`${base}/api/alertas?${q}`, { signal });
  await ensureOk(r, 'Falha ao carregar alertas');
  return r.json() as Promise<AlertasResposta>;
}

const LAST_SEEN_KEY = 'otto-last-seen-at';

export function getLastSeen(): string | null {
  return localStorage.getItem(LAST_SEEN_KEY);
}

export function markSeenNow(): void {
  localStorage.setItem(LAST_SEEN_KEY, new Date().toISOString());
}

export async function fetchDetalhe(numero: string): Promise<{
  oportunidade: Oportunidade;
  eventos: Evento[];
  acompanhamento: Acompanhamento;
  aviso_dados?: string;
}> {
  const r = await fetch(`${base}/api/oportunidades/${encodeURIComponent(numero)}`);
  await ensureOk(r, 'Oportunidade não encontrada');
  return r.json() as Promise<{
    oportunidade: Oportunidade;
    eventos: Evento[];
    acompanhamento: Acompanhamento;
    aviso_dados?: string;
  }>;
}

export async function saveAcompanhamento(
  numero: string,
  body: AcompanhamentoUpdate,
): Promise<{ acompanhamento: Acompanhamento; aviso: string }> {
  const r = await fetch(`${base}/api/oportunidades/${encodeURIComponent(numero)}/acompanhamento`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  await ensureOk(r, 'Falha ao salvar acompanhamento');
  return r.json() as Promise<{ acompanhamento: Acompanhamento; aviso: string }>;
}

export async function fetchAcompanhamentoLista(filtro: FiltroAcompanhamento): Promise<{
  items: { oportunidade: Oportunidade; acompanhamento: Acompanhamento }[];
  contagens: Record<string, number>;
  aviso: string;
}> {
  const q = new URLSearchParams({ filtro, limit: '200' });
  const r = await fetch(`${base}/api/acompanhamento?${q}`);
  await ensureOk(r, 'Falha ao carregar acompanhamento');
  return r.json() as Promise<{
    items: { oportunidade: Oportunidade; acompanhamento: Acompanhamento }[];
    contagens: Record<string, number>;
    aviso: string;
  }>;
}

export async function fetchContagensAcompanhamento(): Promise<Record<string, number>> {
  const r = await fetch(`${base}/api/acompanhamento/contagens`);
  await ensureOk(r, 'Falha ao carregar contagens');
  return r.json() as Promise<Record<string, number>>;
}

function oppPath(numero: string, suffix: string): string {
  return `${base}/api/oportunidades/${encodeURIComponent(numero)}${suffix}`;
}

export async function fetchAnalise(numero: string): Promise<{
  ficha: import('./types').AnaliseFicha;
  documentos: import('./types').DocumentoMeta[];
  checklist: import('./types').ChecklistItem[];
  fluxo: import('./types').FluxoOportunidade;
  cenarios: import('./types').CenarioFinanceiro[];
  fluxo_caixa?: {
    eventos: { data: string; tipo: string; cenario: string; valor: number | null }[];
    aviso?: string;
  };
  ia_disponivel: boolean;
}> {
  const r = await fetch(oppPath(numero, '/analise'));
  await ensureOk(r, 'Falha ao carregar análise');
  return r.json();
}

export async function confirmarRevisaoFicha(numero: string): Promise<void> {
  const r = await fetch(oppPath(numero, '/analise/confirmar-revisao'), { method: 'POST' });
  await ensureOk(r, 'Falha ao confirmar revisão');
}

export async function checklistFromCampo(numero: string, chave: string): Promise<void> {
  const r = await fetch(oppPath(numero, `/analise/campos/${encodeURIComponent(chave)}/checklist`), {
    method: 'POST',
  });
  await ensureOk(r, 'Falha ao criar checklist a partir do campo');
}

export async function saveFluxo(
  numero: string,
  body: Partial<import('./types').FluxoOportunidade>,
): Promise<import('./types').FluxoOportunidade> {
  const r = await fetch(oppPath(numero, '/fluxo'), {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  await ensureOk(r, 'Falha ao salvar fluxo');
  return r.json();
}

export async function createCenario(
  numero: string,
  body: Record<string, unknown>,
): Promise<import('./types').CenarioFinanceiro> {
  const r = await fetch(oppPath(numero, '/financeiro'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  await ensureOk(r, 'Falha ao criar cenário');
  const j = (await r.json()) as { cenario: import('./types').CenarioFinanceiro };
  return j.cenario;
}

export async function updateCenario(
  numero: string,
  id: number,
  body: Record<string, unknown>,
): Promise<import('./types').CenarioFinanceiro> {
  const r = await fetch(oppPath(numero, `/financeiro/${id}`), {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  await ensureOk(r, 'Falha ao atualizar cenário');
  const j = (await r.json()) as { cenario: import('./types').CenarioFinanceiro };
  return j.cenario;
}

export async function listBackups(): Promise<{ items: { nome: string; bytes: number }[] }> {
  const r = await fetch(`${base}/api/backup`);
  await ensureOk(r, 'Falha ao listar backups');
  return r.json();
}

export async function createBackup(): Promise<{ nome: string; arquivo: string }> {
  const r = await fetch(`${base}/api/backup`, { method: 'POST' });
  await ensureOk(r, 'Falha ao criar backup');
  return r.json();
}

export async function restoreBackupCopy(nome: string): Promise<{ aviso: string; destino: string }> {
  const q = new URLSearchParams({ nome });
  const r = await fetch(`${base}/api/backup/restaurar-em-copia?${q}`, { method: 'POST' });
  await ensureOk(r, 'Falha na requisição');
  return r.json();
}

export async function fetchOrgaos(opts?: { q?: string; uf?: string; limit?: number }) {
  const q = new URLSearchParams();
  if (opts?.q) q.set('q', opts.q);
  if (opts?.uf) q.set('uf', opts.uf);
  if (opts?.limit) q.set('limit', String(opts.limit));
  const r = await fetch(`${base}/api/orgaos?${q}`);
  await ensureOk(r, 'Falha ao listar órgãos');
  return r.json() as Promise<{
    items: {
      orgao_chave: string;
      cnpj?: string | null;
      nome: string;
      ufs: string[];
      n_oportunidades: number;
      setores_observados: string[];
      valor_estimado_soma?: number | null;
      periodo_publicacao?: { de?: string | null; ate?: string | null };
    }[];
    total: number;
    aviso: string;
    limitacoes: string[];
  }>;
}

export async function fetchOrgao(chave: string) {
  const r = await fetch(`${base}/api/orgaos/${encodeURIComponent(chave)}`);
  await ensureOk(r, 'Órgão não encontrado');
  return r.json() as Promise<{
    orgao: {
      orgao_chave: string;
      cnpj?: string | null;
      nome: string;
      ufs: string[];
      valor_estimado_soma?: number | null;
      periodo_publicacao?: { de?: string | null; ate?: string | null };
    };
    categorias_observadas: { rotulo: string; quantidade: number }[];
    oportunidades: {
      numero_controle_pncp: string;
      objeto_compra: string;
      uf: string;
      data_publicacao?: string | null;
      nicho_legado: string;
    }[];
    anotacoes: string;
    historico_disponivel: { n_registros: number };
    aviso: string;
  }>;
}

export async function saveOrgaoAnotacoes(
  chave: string,
  body: { anotacoes: string; nome?: string; cnpj?: string | null },
) {
  const r = await fetch(`${base}/api/orgaos/${encodeURIComponent(chave)}/anotacoes`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  await ensureOk(r, 'Falha ao salvar anotação');
  return r.json();
}

export async function fetchVisaoCategorias() {
  const r = await fetch(`${base}/api/visoes/categorias`);
  await ensureOk(r, 'Falha categorias');
  return r.json() as Promise<{
    items: { setor: string; categoria: string; quantidade: number }[];
    aviso: string;
    limitacoes: string[];
  }>;
}

export async function fetchVisaoRegiao() {
  const r = await fetch(`${base}/api/visoes/regiao`);
  await ensureOk(r, 'Falha regiões');
  return r.json() as Promise<{
    items: {
      uf: string;
      quantidade: number;
      valor_estimado_soma?: number | null;
      periodo_publicacao?: { de?: string | null; ate?: string | null };
    }[];
    aviso: string;
    limitacoes: string[];
  }>;
}

export async function fetchIndicadores() {
  const r = await fetch(`${base}/api/indicadores/explorar`);
  await ensureOk(r, 'Falha indicadores');
  return r.json() as Promise<{
    base_calculo: string;
    periodo: { de?: string | null; ate?: string | null };
    total_oportunidades: number;
    com_valor_estimado: number;
    pct_com_valor_estimado: number;
    top_setores: { setor: string; categoria: string; quantidade: number }[];
    limitacoes: string[];
    aviso: string;
  }>;
}

export async function fetchConcorrencia() {
  const r = await fetch(`${base}/api/concorrencia`);
  await ensureOk(r, 'Falha concorrência');
  return r.json() as Promise<{
    dados_suficientes: boolean;
    mensagem: string;
    detalhe?: string | null;
    integracao_faltante?: string | null;
    oportunidades_inspecionadas: number;
    chaves_relevantes_encontradas: string[];
    limitacoes: string[];
  }>;
}

export async function fetchConfiguracoes() {
  const r = await fetch(`${base}/api/configuracoes`);
  await ensureOk(r, 'Falha configurações');
  return r.json() as Promise<{
    data_dir: string;
    db_path: string;
    documentos_dir: string;
    backups_dir: string;
    ia_analise: boolean;
    ocr: boolean;
    ocr_disponivel?: boolean;
    ocr_status?: {
      autorizado: boolean;
      disponivel: boolean;
      aviso: string;
      motor?: string | null;
    };
    docx: boolean;
    download_automatico_anexos: boolean;
    perfil_obrigatorio: boolean;
    restore_operacional: { disponivel_na_ui: boolean; procedimento: string };
    cobertura: unknown;
    aviso: string;
  }>;
}

export type IngestStatus = {
  em_andamento: boolean;
  run_atual: IngestRun | null;
  ultima_execucao: IngestRun | null;
  config: {
    ufs: string[];
    modalidades: number[];
    janela_dias_padrao: number;
    days_min: number;
    days_max: number;
  };
  aviso: string;
};

export type IngestRun = {
  id: number;
  iniciado_em: string;
  finalizado_em: string | null;
  ufs: string | null;
  data_inicial: string | null;
  data_final: string | null;
  total_bruto: number | null;
  total_novos: number | null;
  total_atualizados: number | null;
  erros: number | null;
  mensagem: string | null;
};

export async function fetchIngestStatus(): Promise<IngestStatus> {
  const r = await fetch(`${base}/api/ingest`);
  await ensureOk(r, 'Falha ao ler status da coleta');
  return r.json() as Promise<IngestStatus>;
}

export async function startIngest(opts?: {
  days?: number;
  uf?: string;
}): Promise<{ id: number; status: string; aviso?: string; days?: number; ufs?: string[] }> {
  const q = new URLSearchParams();
  if (opts?.days != null) q.set('days', String(opts.days));
  if (opts?.uf) q.set('uf', opts.uf);
  const r = await fetch(`${base}/api/ingest?${q}`, { method: 'POST' });
  if (r.status === 409) throw new Error('Já existe uma coleta em andamento.');
  await ensureOk(r, 'Falha ao iniciar coleta');
  return r.json();
}

export async function fetchOrientacao(numero: string) {
  const r = await fetch(oppPath(numero, '/orientacao'));
  await ensureOk(r, 'Falha orientação');
  return r.json() as Promise<{
    items: { id: string; texto: string; resposta: string; detalhe: string }[];
    aviso: string;
  }>;
}

export async function saveOrientacao(
  numero: string,
  perguntaId: string,
  body: { resposta: string; detalhe?: string },
) {
  const r = await fetch(oppPath(numero, `/orientacao/${encodeURIComponent(perguntaId)}`), {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  await ensureOk(r, 'Falha ao guardar orientação');
  return r.json() as Promise<{
    items: { id: string; texto: string; resposta: string; detalhe: string }[];
    aviso: string;
  }>;
}

export type RequisitoItem = {
  id: number;
  descricao: string;
  estado: string;
  origem?: string;
  evidencia_documento_id?: number | null;
  evidencia_pagina?: number | null;
  evidencia_trecho: string;
  precisa_revisao?: boolean;
  revisao_origem?: string;
  observacao: string;
  evidencia_documento?: {
    id: number;
    nome_original: string;
    versao: number;
    tipo_mime: string;
    documento_anterior_id?: number | null;
    pagina_aplicavel?: boolean;
  } | null;
};

export async function fetchRequisitos(numero: string) {
  const r = await fetch(oppPath(numero, '/requisitos'));
  await ensureOk(r, 'Falha requisitos');
  return r.json() as Promise<{
    items: RequisitoItem[];
    aviso: string;
  }>;
}

export async function createRequisito(
  numero: string,
  body: { descricao: string; origem?: string; estado?: string },
) {
  const r = await fetch(oppPath(numero, '/requisitos'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  await ensureOk(r, 'Falha ao criar requisito');
  return r.json() as Promise<{
    item: { id: number; descricao: string; estado: string };
    items: {
      id: number;
      descricao: string;
      estado: string;
      evidencia_trecho: string;
      observacao: string;
    }[];
    aviso: string;
  }>;
}

export async function createOportunidadeManual(body: {
  objeto_compra: string;
  orgao_razao_social?: string;
  uf?: string;
  municipio?: string;
  modalidade?: string;
  valor_total_estimado?: number | null;
  data_encerramento?: string | null;
}) {
  const r = await fetch(`${base}/api/oportunidades/manual`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  await ensureOk(r, 'Falha no cadastro manual');
  return r.json() as Promise<{
    item: import('./types').Oportunidade;
    aviso: string;
  }>;
}

export async function importOportunidadesManualJson(payload: unknown) {
  const r = await fetch(`${base}/api/oportunidades/manual/import`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  await ensureOk(r, 'Falha na importação');
  return r.json() as Promise<{
    criados: string[];
    erros: { indice: number; erro: string }[];
    aviso: string;
  }>;
}

export async function fetchResultados() {
  const r = await fetch(`${base}/api/resultados`);
  await ensureOk(r, 'Falha ao carregar resultados');
  return r.json() as Promise<{
    items: {
      oportunidade: import('./types').Oportunidade;
      estado_fluxo: string;
      resultado_disputa: string;
      resultado_contratacao: string;
      resultado_execucao: string;
      resultado_recebimento: string;
      tempo_preparacao_horas: number | null;
      custo_preparacao: number | null;
    }[];
    count: number;
    aviso: string;
  }>;
}

export async function fetchAuditoria() {
  const r = await fetch(`${base}/api/auditoria`);
  await ensureOk(r, 'Falha na auditoria');
  return r.json() as Promise<{
    items: {
      id: number;
      acao: string;
      numero_controle_pncp: string | null;
      detalhe: string;
      criado_em: string;
    }[];
    aviso: string;
  }>;
}

export type AprendizadoResumo = {
  acoes: {
    total: number;
    por_acao: { acao: string; n: number }[];
    ultimas: {
      id: number;
      acao: string;
      numero_controle_pncp: string | null;
      detalhe: string;
      criado_em: string;
    }[];
  };
  ia_sugestoes: {
    total: number;
    aplicadas: number;
    rejeitadas: number;
    pendentes: number;
    taxa_aceitacao: number | null;
    por_tipo_aplicadas: { tipo: string; n: number }[];
    amostras_aplicadas: {
      id: number;
      tipo: string;
      chave: string;
      titulo: string;
      valor: string;
      numero_controle_pncp: string;
      criado_em: string;
    }[];
    amostras_rejeitadas: {
      id: number;
      tipo: string;
      chave: string;
      titulo: string;
      valor: string;
      numero_controle_pncp: string;
      criado_em: string;
    }[];
  };
  resultados: {
    com_resultado: number;
    por_disputa: { valor: string; n: number }[];
    por_estado_fluxo: { valor: string; n: number }[];
  };
  insights: string[];
  aviso: string;
  nuvem: boolean;
  altera_modelo: boolean;
  influencia_prompt_local?: boolean;
  influencia_analise?: {
    ativa: boolean;
    decisoes: number;
    minimo: number;
    chaves_preferidas: string[];
    chaves_evitar: string[];
    resumo_prompt: string;
  };
};

export async function fetchAprendizado() {
  const r = await fetch(`${base}/api/aprendizado`);
  await ensureOk(r, 'Falha ao carregar aprendizado do histórico');
  return r.json() as Promise<AprendizadoResumo>;
}

export async function patchPrazosManuais(
  numero: string,
  body: {
    data_esclarecimento?: string | null;
    data_impugnacao?: string | null;
    limpar_esclarecimento?: boolean;
    limpar_impugnacao?: boolean;
  },
) {
  const r = await fetch(oppPath(numero, '/prazos-manuais'), {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  await ensureOk(r, 'Falha ao gravar prazos manuais');
  return r.json() as Promise<{ item: import('./types').Oportunidade; aviso: string }>;
}

export async function gerarRequisitosDaFicha(numero: string) {
  const r = await fetch(oppPath(numero, '/requisitos/gerar-da-ficha'), { method: 'POST' });
  await ensureOk(r, 'Falha ao gerar requisitos da ficha');
  return r.json() as Promise<{
    items: {
      id: number;
      descricao: string;
      estado: string;
      evidencia_documento_id?: number | null;
      evidencia_trecho: string;
      observacao: string;
      origem?: string;
    }[];
    aviso: string;
    gerados?: number;
  }>;
}

export async function fetchFluxoVista(estado: string) {
  const r = await fetch(`${base}/api/fluxo?estado=${encodeURIComponent(estado)}`);
  await ensureOk(r, 'Falha na vista de fluxo');
  return r.json() as Promise<{
    estado: string;
    items: { oportunidade: import('./types').Oportunidade; estado_fluxo: string }[];
    count: number;
    contagens: Record<string, number>;
    aviso: string;
  }>;
}

export async function fetchItensLotes(numero: string) {
  const r = await fetch(oppPath(numero, '/itens-lotes'));
  await ensureOk(r, 'Falha itens/lotes');
  return r.json() as Promise<{
    lotes: {
      id: number;
      codigo: string;
      descricao: string;
      disputa_separada_confirmada: boolean;
    }[];
    itens: {
      id: number;
      lote_id: number | null;
      descricao: string;
      quantidade: number | null;
      unidade: string;
      setor?: string;
      categoria?: string;
      setor_sugerido?: string;
      categoria_sugerida?: string;
      classificacao_origem?: string;
    }[];
    aviso: string;
  }>;
}

export async function createLote(
  numero: string,
  body: { descricao?: string; codigo?: string; disputa_separada_confirmada?: boolean },
) {
  const r = await fetch(oppPath(numero, '/lotes'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  await ensureOk(r, 'Falha ao criar lote');
  return r.json() as Promise<Awaited<ReturnType<typeof fetchItensLotes>>>;
}

export async function patchLote(
  numero: string,
  loteId: number,
  body: { disputa_separada_confirmada?: boolean; descricao?: string },
) {
  const r = await fetch(oppPath(numero, `/lotes/${loteId}`), {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  await ensureOk(r, 'Falha ao atualizar lote');
  return r.json() as Promise<Awaited<ReturnType<typeof fetchItensLotes>>>;
}

export async function createItem(
  numero: string,
  body: {
    descricao: string;
    lote_id?: number | null;
    setor?: string;
    categoria?: string;
  },
) {
  const r = await fetch(oppPath(numero, '/itens'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  await ensureOk(r, 'Falha ao criar item');
  return r.json() as Promise<Awaited<ReturnType<typeof fetchItensLotes>>>;
}

export async function patchItem(
  numero: string,
  itemId: number,
  body: { setor?: string; categoria?: string; descricao?: string; observacao?: string },
) {
  const r = await fetch(oppPath(numero, `/itens/${itemId}`), {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  await ensureOk(r, 'Falha ao atualizar item');
  return r.json() as Promise<Awaited<ReturnType<typeof fetchItensLotes>>>;
}

export async function patchRequisito(
  numero: string,
  id: number,
  body: {
    estado?: string;
    evidencia_documento_id?: number | null;
    limpar_evidencia_doc?: boolean;
    evidencia_pagina?: number | null;
    limpar_evidencia_pagina?: boolean;
    evidencia_trecho?: string;
    observacao?: string;
    descricao?: string;
    confirmar_revisao_usuario?: boolean;
  },
) {
  const r = await fetch(oppPath(numero, `/requisitos/${id}`), {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  await ensureOk(r, 'Falha ao atualizar requisito');
  return r.json() as Promise<{
    item: RequisitoItem;
    items: RequisitoItem[];
    aviso: string;
  }>;
}

export async function checklistFromRequisito(numero: string, reqId: number): Promise<void> {
  const r = await fetch(oppPath(numero, `/requisitos/${reqId}/checklist`), {
    method: 'POST',
  });
  await ensureOk(r, 'Falha ao criar tarefa a partir do requisito');
}

export async function fetchClassificacoes(numero: string) {
  const r = await fetch(oppPath(numero, '/classificacoes'));
  await ensureOk(r, 'Falha classificações');
  return r.json() as Promise<{ items: { setor: string; categoria: string; origem: string }[] }>;
}

export async function addClassificacao(
  numero: string,
  body: { setor: string; categoria?: string; subcategoria?: string },
) {
  const r = await fetch(oppPath(numero, '/classificacoes'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  await ensureOk(r, 'Falha na requisição');
  return r.json();
}

export type IaStatus = {
  disponivel: boolean;
  runtime?: string;
  base_url?: string;
  modelo_configurado?: string;
  modelo_presente?: boolean;
  modelos_locais?: string[];
  aviso?: string;
  nuvem?: boolean;
  fluxo_manual_sempre_disponivel?: boolean;
};

export type IaSugestao = {
  id: number;
  job_id: number;
  tipo: string;
  chave: string;
  titulo: string;
  valor: string;
  documento_id?: number | null;
  documento_versao?: number | null;
  documento_nome?: string;
  documento_mime?: string;
  pagina?: number | null;
  trecho: string;
  referencia_confirmada: boolean;
  status_evidencia?: 'confirmada' | 'nao_confirmada' | string;
  aviso_referencia: string;
  estado: string;
  aplicavel?: boolean;
};

export type IaJob = {
  id: number;
  status: string;
  documento_ids: number[];
  modelo: string;
  progresso: string;
  cobertura: string;
  erro: string;
  sugestoes?: IaSugestao[];
};

export async function fetchIaAnalise(numero: string) {
  const r = await fetch(oppPath(numero, '/ia-analise'));
  await ensureOk(r, 'Falha ao carregar análise IA local');
  return r.json() as Promise<{
    status: IaStatus;
    jobs: IaJob[];
    sugestoes_pendentes: IaSugestao[];
    aviso: string;
  }>;
}

export async function fetchIaJob(numero: string, jobId: number) {
  const r = await fetch(oppPath(numero, `/ia-analise/jobs/${jobId}`));
  await ensureOk(r, 'Falha ao consultar job IA');
  return r.json() as Promise<IaJob>;
}

export async function iniciarIaAnalise(numero: string, documentoIds: number[]) {
  const r = await fetch(oppPath(numero, '/ia-analise'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ documento_ids: documentoIds }),
  });
  await ensureOk(r, 'Falha ao iniciar IA local');
  return r.json() as Promise<{ job: IaJob; status: IaStatus }>;
}

export async function aplicarSugestaoIa(
  numero: string,
  sugId: number,
  body?: { forcar_sobrescrita_usuario?: boolean },
) {
  const r = await fetch(oppPath(numero, `/ia-analise/sugestoes/${sugId}/aplicar`), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body || {}),
  });
  await ensureOk(r, 'Falha ao aplicar sugestão');
  return r.json();
}

export async function rejeitarSugestaoIa(numero: string, sugId: number) {
  const r = await fetch(oppPath(numero, `/ia-analise/sugestoes/${sugId}/rejeitar`), {
    method: 'POST',
  });
  await ensureOk(r, 'Falha ao rejeitar sugestão');
  return r.json();
}

export async function uploadDocumento(
  numero: string,
  file: File,
): Promise<{ documento: import('./types').DocumentoMeta; aviso: string }> {
  const fd = new FormData();
  fd.append('arquivo', file);
  const r = await fetch(oppPath(numero, '/documentos'), { method: 'POST', body: fd });
  await ensureOk(r, 'Falha no upload');
  return r.json();
}

export function documentoArquivoUrl(numero: string, docId: number): string {
  return oppPath(numero, `/documentos/${docId}/arquivo`);
}

export async function fetchDocumentoPaginas(
  numero: string,
  docId: number,
): Promise<{ paginas: { pagina: number; texto: string }[]; aviso: string }> {
  const r = await fetch(oppPath(numero, `/documentos/${docId}/paginas`));
  await ensureOk(r, 'Falha ao ler páginas');
  return r.json();
}

export async function reprocessarDocumentoOcr(
  numero: string,
  docId: number,
): Promise<{ documento: import('./types').DocumentoMeta; aviso: string }> {
  const r = await fetch(oppPath(numero, `/documentos/${docId}/ocr`), { method: 'POST' });
  await ensureOk(r, 'Falha ao reprocessar OCR');
  return r.json();
}

export type AnexoRemoto = {
  sequencial_documento: number | null;
  titulo: string;
  tipo: string;
  url: string;
  baixavel: boolean;
  ja_local: boolean;
  motivo_nao_baixavel?: string | null;
  nome_sugerido?: string | null;
};

export async function fetchAnexosRemotos(numero: string): Promise<{
  items: AnexoRemoto[];
  aviso: string;
  compra?: { cnpj: string; ano: number; sequencial: number };
}> {
  const r = await fetch(oppPath(numero, '/anexos-remotos'));
  await ensureOk(r, 'Falha ao listar anexos PNCP');
  return r.json();
}

export async function baixarAnexosRemotos(
  numero: string,
  opts?: { sequenciais?: number[]; max_arquivos?: number },
): Promise<{
  baixados: { documento_id: number; nome: string; status_extracao: string }[];
  erros: { titulo?: string; erro: string }[];
  pulados: { titulo?: string; motivo?: string }[];
  aviso: string;
}> {
  const r = await fetch(oppPath(numero, '/anexos-remotos/baixar'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(opts || {}),
  });
  await ensureOk(r, 'Falha ao baixar anexos');
  return r.json();
}

export async function saveAnaliseCampo(
  numero: string,
  chave: string,
  body: {
    valor: string;
    natureza?: import('./types').NaturezaCampo;
    documento_id?: number | null;
    pagina?: number | null;
    trecho?: string;
    limpar_revisao?: boolean;
  },
): Promise<void> {
  const r = await fetch(oppPath(numero, `/analise/campos/${encodeURIComponent(chave)}`), {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ natureza: 'usuario', trecho: '', limpar_revisao: true, ...body }),
  });
  await ensureOk(r, 'Falha ao salvar campo');
}

export async function createChecklistItem(
  numero: string,
  body: { titulo: string; descricao?: string; requisito_chave?: string; categoria?: string },
): Promise<import('./types').ChecklistItem> {
  const r = await fetch(oppPath(numero, '/checklist'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  await ensureOk(r, 'Falha ao criar item');
  const j = (await r.json()) as { item: import('./types').ChecklistItem };
  return j.item;
}

export async function patchChecklistItem(
  numero: string,
  itemId: number,
  body: Partial<{
    status: string;
    titulo: string;
    descricao: string;
    prazo_conhecido: string;
    responsavel: string;
    categoria: string;
    observacao: string;
  }>,
): Promise<import('./types').ChecklistItem> {
  const r = await fetch(oppPath(numero, `/checklist/${itemId}`), {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  await ensureOk(r, 'Falha ao atualizar item');
  const j = (await r.json()) as { item: import('./types').ChecklistItem };
  return j.item;
}

export function fmtMoney(v?: number | null): string {
  if (v == null) return '—';
  return v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 });
}

export function fmtDate(iso?: string | null): string {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('pt-BR');
}
