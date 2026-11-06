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

/** Cadastros manuais de teste — fora de destaque/KPIs (e da lista do radar). */
export function isRegistroTeste(o: Oportunidade): boolean {
  if (o.origem_registro !== 'manual') return false;
  const obj = (o.objeto_compra || '').trim();
  return (
    obj.toUpperCase().startsWith('TESTE') || obj.startsWith('Import JSON teste')
  );
}

/** Label de categoria na tabela: nao_classificado → Outros. */
export function labelCategoria(o: Oportunidade): string {
  const raw =
    (o.categoria_principal && o.categoria_principal.trim()) ||
    (o.nicho && o.nicho.trim()) ||
    '';
  if (!raw || raw === 'nao_classificado') return 'Outros';
  return raw;
}

/**
 * Filtro de prazo:
 * - sempre exclui vencidas (daysUntil < 0);
 * - `abertas`: não vencidas (sem data permanece);
 * - dias < 3650: exige data e daysUntil ∈ [0, dias];
 * - dias ≥ 3650: qualquer prazo não vencido (sem data ok).
 */
export type FiltroPrazo = number | 'abertas';

export function passaFiltroPrazo(o: Oportunidade, dias: FiltroPrazo): boolean {
  const d = daysUntil(o.data_encerramento);
  if (d !== null && d < 0) return false;
  if (dias === 'abertas') return true;
  if (dias < 3650) {
    if (d === null) return false;
    return d <= dias;
  }
  return true;
}

/** Contagem alinhada ao KPI “Prazo ≤ N dias” (mesma regra do filtro). */
export function countPrazoAte(items: Oportunidade[], diasMax: number): number {
  return items.filter((o) => passaFiltroPrazo(o, diasMax)).length;
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
    if (o.nicho && o.nicho !== 'outros' && o.nicho !== 'nao_classificado') parts.push(`Nicho: ${o.nicho}`);
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
  opts: { q: string; dias: FiltroPrazo; somenteAlta: boolean; ocultarTestes?: boolean },
): Oportunidade[] {
  const q = opts.q.trim().toLowerCase();
  const ocultarTestes = opts.ocultarTestes !== false;
  return items.filter((o) => {
    if (ocultarTestes && isRegistroTeste(o)) return false;
    if (opts.somenteAlta && o.confianca_classificacao !== 'alta') return false;
    if (!passaFiltroPrazo(o, opts.dias)) return false;
    if (!q) return true;
    const hay = `${o.objeto_compra} ${o.orgao_razao_social} ${getMunicipio(o)}`.toLowerCase();
    return hay.includes(q);
  });
}

export function computeKpisExtras(items: Oportunidade[]) {
  const alta = items.filter((o) => o.confianca_classificacao === 'alta');
  const orgaos = new Set(items.map((o) => o.orgao_razao_social));
  const scoreMedio =
    items.length > 0 ? items.reduce((s, o) => s + o.score_total, 0) / items.length : 0;
  return {
    altaConfianca: alta.length,
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
  const sorted = items.filter((o) => !isRegistroTeste(o));
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
  // Lista geral: não usar score TI — respeitar ordenação ativa.
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
