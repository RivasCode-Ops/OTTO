import { fmtDate } from '../api';
import type { Cobertura } from '../types';
import { diasDesdeColeta } from '../utils';

type Props = {
  cobertura: Cobertura | null;
  ordenacaoRotulo: string;
  modo: 'geral' | 'ti';
};

export function CoverageBanner({ cobertura, ordenacaoRotulo, modo }: Props) {
  if (!cobertura) return null;
  const cfg = cobertura.config_coleta;
  const ufs = (cfg.ufs || []).join(', ') || 'não configurada';
  const mods = (cfg.modalidades || []).join(', ') || 'não configurada';
  const ult = cobertura.ultima_execucao;
  const ufsBanco = (cobertura.banco.ufs_presentes || []).join(', ') || 'nenhuma';
  const nichos = (cobertura.banco.por_nicho || [])
    .map((n) => `${n.nicho} (${n.quantidade})`)
    .join(', ');

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
