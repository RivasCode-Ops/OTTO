import type { Oportunidade } from './types';

export function getMunicipio(o: Oportunidade): string {
  const nome = o.raw_json?.unidadeOrgao?.municipioNome;
  if (typeof nome === 'string' && nome.trim()) return nome;
  if (o.municipio_ibge) return o.municipio_ibge;
  return '—';
}

/** Interpreta YYYY-MM-DD (ou prefixo ISO) como data civil local — evita UTC midnight. */
function parseDataLocal(iso: string): Date | null {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso.trim());
  if (m) {
    const y = Number(m[1]);
    const mo = Number(m[2]) - 1;
    const d = Number(m[3]);
    const dt = new Date(y, mo, d);
    return Number.isNaN(dt.getTime()) ? null : dt;
  }
  const end = new Date(iso);
  return Number.isNaN(end.getTime()) ? null : end;
}

export function daysUntil(iso?: string | null): number | null {
  if (!iso) return null;
  const end = parseDataLocal(iso);
  if (!end) return null;
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  end.setHours(0, 0, 0, 0);
  return Math.round((end.getTime() - now.getTime()) / 86400000);
}

/**
 * Cadastros de teste: prefixo MANUAL- no número, ou manual com objeto
 * TESTE… / Import JSON teste…
 */
export function isRegistroTeste(o: Oportunidade): boolean {
  const num = (o.numero_controle_pncp || '').trim();
  if (num.toUpperCase().startsWith('MANUAL-')) return true;
  if (o.origem_registro !== 'manual') return false;
  const obj = (o.objeto_compra || '').trim();
  return (
    obj.toUpperCase().startsWith('TESTE') || obj.startsWith('Import JSON teste')
  );
}

export const NICHO_LABELS: Record<string, string> = {
  ti_software: 'TI / software',
  saude_medicamentos: 'Saúde / medicamentos',
  obras_engenharia: 'Obras / engenharia',
  passagens_viagens: 'Passagens / viagens',
  alimentos_merenda: 'Alimentos / merenda',
  material_escritorio_papelaria: 'Material de escritório',
  limpeza_conservacao: 'Limpeza / conservação',
  veiculos_combustiveis: 'Veículos / combustíveis',
  outros: 'Outros',
};

export function labelNicho(nicho: string | null | undefined): string {
  if (!nicho) return 'Outros';
  return NICHO_LABELS[nicho] || nicho;
}

/** Label de categoria/nicho na UI: slugs → rótulo amigável (select Nicho). */
export function labelCategoria(o: Oportunidade): string {
  const cat = (o.categoria_principal && o.categoria_principal.trim()) || '';
  if (cat && NICHO_LABELS[cat]) return NICHO_LABELS[cat];
  // Rótulo livre (ex.: "TI") tem prioridade; slug com underscore cai no mapa de nicho.
  if (cat && cat !== 'nao_classificado' && !/^[a-z0-9]+(_[a-z0-9]+)+$/i.test(cat)) {
    return cat;
  }
  const nicho = (o.nicho && o.nicho.trim()) || '';
  if (!nicho || nicho === 'nao_classificado') return 'Outros';
  return labelNicho(nicho);
}

/**
 * Filtro de prazo:
 * - `abertas`: exclui vencidas; sem data permanece;
 * - dias < 3650: exige data e daysUntil ∈ [0, dias] (exclui vencidas e sem prazo);
 * - dias ≥ 3650 (Qualquer prazo): inclui vencidas e sem prazo.
 */
export type FiltroPrazo = number | 'abertas';

export function passaFiltroPrazo(o: Oportunidade, dias: FiltroPrazo): boolean {
  const d = daysUntil(o.data_encerramento);
  if (dias === 'abertas') {
    return !(d !== null && d < 0);
  }
  if (dias < 3650) {
    if (d === null) return false;
    if (d < 0) return false;
    return d <= dias;
  }
  // Qualquer prazo: tudo.
  return true;
}

/** Contagem alinhada ao KPI “Prazo ≤ N dias” (mesma regra do filtro). */
export function countPrazoAte(items: Oportunidade[], diasMax: number): number {
  return items.filter((o) => passaFiltroPrazo(o, diasMax)).length;
}

/**
 * KPI Oportunidades: total no escopo da lista — nunca o length da página filtrada.
 * DECISÃO (2026-11-06): com escopo `config`, não cair no total do banco inteiro
 * (histórico de outras UFs); preferir total_no_escopo da cobertura se /api/kpis
 * ainda devolver o total global (API antiga / worker órfão).
 */
export function resolveKpiTotalBanco(opts: {
  kpisTotal?: number | null;
  /** total_no_escopo da cobertura (UFs da coleta). */
  coberturaEscopoTotal?: number | null;
  /** banco.total_oportunidades (todas as UFs no SQLite). */
  coberturaBancoTotal?: number | null;
  /** @deprecated use coberturaBancoTotal / coberturaEscopoTotal */
  coberturaTotal?: number | null;
  escopoUf?: 'config' | 'todas';
}): number {
  const escopo = opts.escopoUf ?? 'config';
  const bancoTotal =
    typeof opts.coberturaBancoTotal === 'number' && Number.isFinite(opts.coberturaBancoTotal)
      ? opts.coberturaBancoTotal
      : typeof opts.coberturaTotal === 'number' && Number.isFinite(opts.coberturaTotal)
        ? opts.coberturaTotal
        : null;
  const escopoTotal =
    typeof opts.coberturaEscopoTotal === 'number' && Number.isFinite(opts.coberturaEscopoTotal)
      ? opts.coberturaEscopoTotal
      : null;
  const kpisTotal =
    typeof opts.kpisTotal === 'number' && Number.isFinite(opts.kpisTotal) ? opts.kpisTotal : null;

  if (escopo === 'todas') {
    if (kpisTotal != null) return kpisTotal;
    if (bancoTotal != null) return bancoTotal;
    return 0;
  }

  // config: se KPI == banco inteiro e cobertura tem escopo menor, KPI ignorou o filtro
  if (kpisTotal != null) {
    if (
      escopoTotal != null &&
      bancoTotal != null &&
      kpisTotal === bancoTotal &&
      escopoTotal < bancoTotal
    ) {
      return escopoTotal;
    }
    return kpisTotal;
  }
  if (escopoTotal != null) return escopoTotal;
  return 0;
}

export type ScoreTier = 'high' | 'mid' | 'low';

export function scoreTier(score: number): ScoreTier {
  if (score >= 65) return 'high';
  if (score >= 40) return 'mid';
  return 'low';
}

export function highlightReason(o: Oportunidade, modo: 'geral' | 'ti' = 'geral'): string {
  if (modo === 'geral') {
    const parts: string[] = [];
    if (o.data_publicacao) parts.push(`Publicada ${new Date(o.data_publicacao).toLocaleDateString('pt-BR')}`);
    const d = daysUntil(o.data_encerramento);
    if (d !== null) parts.push(d <= 7 ? 'Prazo de proposta próximo' : 'Com prazo de proposta');
    else parts.push('Prazo de proposta não informado');
    if (o.nicho && o.nicho !== 'outros' && o.nicho !== 'nao_classificado') {
      parts.push(`Nicho: ${labelNicho(o.nicho)}`);
    }
    return parts.slice(0, 3).join(' · ');
  }
  const parts: string[] = [];
  const labels = o.score_detalhe?.labels ?? {};
  if (labels.valor && !labels.valor.includes('R$ 0')) parts.push('Valor relevante');
  if (labels.urgencia?.includes('3 dia') || labels.urgencia?.includes('6 dia') || labels.urgencia?.includes('7 dia')) {
    parts.push('Prazo curto');
  } else if (labels.urgencia) {
    parts.push('Prazo monitorado');
  }
  if (o.confianca_classificacao === 'alta') parts.push('TI alta confiança');
  else parts.push('TI baixa confiança');
  return parts.slice(0, 3).join(' · ');
}

export function filterOportunidades(
  items: Oportunidade[],
  opts: {
    q: string;
    dias: FiltroPrazo;
    somenteAlta: boolean;
    ocultarTestes?: boolean;
    nicho?: string | null;
  },
): Oportunidade[] {
  const q = opts.q.trim().toLowerCase();
  const ocultarTestes = opts.ocultarTestes !== false;
  const nicho = opts.nicho && opts.nicho !== 'todos' ? opts.nicho : null;
  return items.filter((o) => {
    if (ocultarTestes && isRegistroTeste(o)) return false;
    if (nicho && (o.nicho || 'outros') !== nicho) return false;
    if (opts.somenteAlta && o.confianca_classificacao !== 'alta') return false;
    if (!passaFiltroPrazo(o, opts.dias)) return false;
    if (!q) return true;
    const hay = `${o.objeto_compra} ${o.orgao_razao_social} ${getMunicipio(o)}`.toLowerCase();
    return hay.includes(q);
  });
}

/** Rótulo curto do filtro de prazo (KPI / subtítulo). */
export function rotuloFiltroPrazo(dias: FiltroPrazo): string {
  if (dias === 'abertas') return 'abertas';
  if (dias === 3650) return 'qualquer prazo';
  return `prazo ≤${dias}d`;
}

/**
 * Extras dos KPIs.
 * DECISÃO (2026-11-06): "TI alta" = nicho ti_software + confiança alta
 * (não qualquer setor com confianca_classificacao=alta após multi-nicho).
 */
export function computeKpisExtras(items: Oportunidade[]) {
  const tiAlta = items.filter(
    (o) => (o.nicho || '') === 'ti_software' && o.confianca_classificacao === 'alta',
  );
  const orgaos = new Set(items.map((o) => o.orgao_razao_social));
  const scoreMedio =
    items.length > 0 ? items.reduce((s, o) => s + o.score_total, 0) / items.length : 0;
  return {
    altaConfianca: tiAlta.length,
    scoreMedio,
    orgaosAtivos: orgaos.size,
  };
}

export function pickPriority(
  items: Oportunidade[],
  n = 5,
  opts: { modo: 'geral' | 'ti'; ordenacao: 'publicacao' | 'prazo' } = {
    modo: 'geral',
    ordenacao: 'publicacao',
  },
): Oportunidade[] {
  // Caller já aplica ocultar testes / filtros; não filtra de novo aqui.
  const sorted = [...items];
  if (opts.modo === 'ti') {
    const alta = sorted
      .filter((o) => o.confianca_classificacao === 'alta')
      .sort((a, b) => b.score_total - a.score_total);
    if (alta.length >= n) return alta.slice(0, n);
    const rest = sorted
      .filter((o) => o.confianca_classificacao !== 'alta')
      .sort((a, b) => b.score_total - a.score_total);
    return [...alta, ...rest].slice(0, n);
  }
  if (opts.ordenacao === 'prazo') {
    sorted.sort((a, b) => {
      if (!a.data_encerramento && !b.data_encerramento) return 0;
      if (!a.data_encerramento) return 1;
      if (!b.data_encerramento) return -1;
      return a.data_encerramento.localeCompare(b.data_encerramento);
    });
  } else {
    sorted.sort((a, b) => {
      if (!a.data_publicacao && !b.data_publicacao) return 0;
      if (!a.data_publicacao) return 1;
      if (!b.data_publicacao) return -1;
      return b.data_publicacao.localeCompare(a.data_publicacao);
    });
  }
  return sorted.slice(0, n);
}

/** Dias desde a última coleta (finalizado_em || iniciado_em). */
export function diasDesdeColeta(iso?: string | null): number | null {
  if (!iso) return null;
  const then = parseDataLocal(iso);
  if (!then) return null;
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  then.setHours(0, 0, 0, 0);
  return Math.floor((now.getTime() - then.getTime()) / 86400000);
}
