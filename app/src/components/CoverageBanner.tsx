import { fmtDate, type EscopoUf } from '../api';
import type { Cobertura } from '../types';
import { diasDesdeColeta } from '../utils';

type Props = {
  cobertura: Cobertura | null;
  ordenacaoRotulo: string;
  modo: 'geral' | 'ti';
  escopoUf?: EscopoUf;
  /** Contagem na lista atual (UF), sem testes se ocultos — alinha ao KPI. */
  totalEscopoVisivel?: number;
  /** Quantos registros de teste estão ocultos no recorte UF. */
  nTestesOcultos?: number;
};

export function CoverageBanner({
  cobertura,
  ordenacaoRotulo,
  modo,
  escopoUf = 'config',
  totalEscopoVisivel,
  nTestesOcultos = 0,
}: Props) {
  if (!cobertura) return null;
  const cfg = cobertura.config_coleta;
  const ufs = (cfg.ufs || []).join(', ') || 'não configurada';
  const mods = (cfg.modalidades || []).join(', ') || 'não configurada';
  const ult = cobertura.ultima_execucao;
  const ufsBanco = (cobertura.banco.ufs_presentes || []).join(', ') || 'nenhuma';
  const nichos = (cobertura.banco.por_nicho || [])
    .map((n) => `${n.nicho} (${n.quantidade})`)
    .join(', ');
  const escopo = cobertura.escopo_uf;
  const fora = (escopo?.ufs_fora_config || [])
    .map((x) => `${x.uf} (${x.quantidade})`)
    .join(', ');
  // Fallback: se a API antiga não enviar escopo_uf, usa UFs de config_coleta.
  const ufsEscopoLista = (
    escopo?.ufs_config?.length ? escopo.ufs_config : cfg.ufs || []
  )
    .map((u) => String(u).trim().toUpperCase())
    .filter(Boolean);
  const totalNoEscopoBruto =
    typeof escopo?.total_no_escopo === 'number'
      ? escopo.total_no_escopo
      : undefined;
  // Mesma base do KPI quando testes ocultos: totalVisivel (= bruto − testes).
  const totalExibido =
    typeof totalEscopoVisivel === 'number' ? totalEscopoVisivel : totalNoEscopoBruto;
  const notaTestes =
    nTestesOcultos > 0
      ? ` (sem ${nTestesOcultos} teste${nTestesOcultos === 1 ? '' : 's'}; ${totalNoEscopoBruto ?? '—'} no SQLite)`
      : '';
  const rotuloEscopoLista =
    escopoUf === 'todas'
      ? `todas as UFs do banco (${cobertura.banco.total_oportunidades})`
      : escopoUf !== 'config'
        ? `UF ${String(escopoUf).toUpperCase()} — ${totalExibido ?? '—'} na lista${notaTestes}`
        : `UF(s) da coleta${ufsEscopoLista.length ? ` (${ufsEscopoLista.join(', ')})` : ''} — ${totalExibido ?? '—'} no escopo${notaTestes}`;

  const dataUlt = ult?.finalizado_em || ult?.iniciado_em || null;
  const idade = diasDesdeColeta(dataUlt);
  const dadoVelho = idade !== null && idade > 3;

  return (
    <>
      {dadoVelho && dataUlt && (
        <div className="stale-banner" role="status">
          Última coleta há {idade} dia(s) ({fmtDate(dataUlt)}). Considere atualizar em Configurações
          ou pelo agendador.
        </div>
      )}
      <section className="coverage" aria-label="Cobertura da coleta">
        <p className="coverage__aviso">{cobertura.aviso}</p>
        <ul className="coverage__list">
          <li>
            <strong>Fonte:</strong> {cobertura.fonte}
          </li>
          <li>
            <strong>Coleta configurada:</strong> UF(s) {ufs} · modalidade(s) {mods} · janela padrão{' '}
            {cfg.janela_dias_padrao} dia(s)
          </li>
          <li>
            <strong>Escopo da lista:</strong> {rotuloEscopoLista}
            {fora && escopoUf === 'config' ? ` · fora do escopo (histórico): ${fora}` : ''}
          </li>
          <li>
            <strong>No banco local:</strong> {cobertura.banco.total_oportunidades} oportunidade(s) · UF(s){' '}
            {ufsBanco}
            {nichos ? ` · por nicho: ${nichos}` : ''}
          </li>
          <li>
            <strong>Última coleta registrada:</strong>{' '}
            {ult
              ? `${fmtDate(ult.finalizado_em || ult.iniciado_em)} · período ${ult.data_inicial || '—'} a ${ult.data_final || '—'} · ${ult.total_novos ?? 0} novas / ${ult.total_atualizados ?? 0} atualizadas · erros ${ult.erros ?? 0}`
              : 'Nenhuma execução de coleta registrada ainda'}
          </li>
          <li>
            <strong>Visão atual:</strong>{' '}
            {modo === 'ti' ? 'Radar TI (filtro opcional)' : 'Lista geral (todos os setores nos dados)'} ·
            ordenação: {ordenacaoRotulo}
          </li>
          {modo === 'geral' && <li className="coverage__note">{cobertura.ordenacao.sem_prazo}</li>}
        </ul>
      </section>
    </>
  );
}
