import { EmptyState } from './EmptyState';
import { fmtDate, fmtMoney } from '../api';
import type { Oportunidade } from '../types';
import { daysUntil, getMunicipio, highlightReason, labelNicho, scoreTier } from '../utils';

type Props = {
  items: Oportunidade[];
  onSelect: (o: Oportunidade) => void;
  selected?: string | null;
  semDados?: boolean;
  filtroAtivo?: boolean;
  modo: 'geral' | 'ti';
  ordenacaoRotulo: string;
};

export function PriorityCards({
  items,
  onSelect,
  selected,
  semDados,
  filtroAtivo,
  modo,
  ordenacaoRotulo,
}: Props) {
  const geral = modo === 'geral';

  return (
    <section className="priority">
      <header className="section-head">
        <div>
          <h2>{geral ? 'Em destaque' : 'Prioridade agora'}</h2>
          <p className="muted">
            {geral ? `Top 5 pela ordenação ativa · ${ordenacaoRotulo}` : 'Top 5 por score · foco em alta confiança (modo TI)'}
          </p>
        </div>
      </header>

      {items.length === 0 ? (
        <EmptyState
          title={semDados ? 'Lista vazia' : 'Nada no recorte atual'}
          hint={
            semDados
              ? 'Execute otto ingest --days 7 para popular o painel com editais.'
              : filtroAtivo
                ? 'Amplie o período ou ajuste os filtros.'
                : 'Nenhuma oportunidade priorizada neste momento.'
          }
        />
      ) : (
        <div className="priority__grid">
          {items.map((o) => {
            const dias = daysUntil(o.data_encerramento);
            const tier = scoreTier(o.score_total);
            const urgente = dias !== null && dias <= 7;
            return (
              <button
                key={o.numero_controle_pncp}
                type="button"
                className={`priority-card priority-card--${geral ? 'mid' : tier} ${selected === o.numero_controle_pncp ? 'priority-card--selected' : ''}`}
                onClick={() => onSelect(o)}
              >
                <div className="priority-card__head">
                  {geral ? (
                    <span className="conf-pill conf-pill--nicho">{labelNicho(o.nicho)}</span>
                  ) : (
                    <>
                      <span className={`score-badge score-badge--${tier}`}>{o.score_total.toFixed(0)}</span>
                      <span className={`conf-pill conf-pill--${o.confianca_classificacao}`}>
                        {o.confianca_classificacao}
                      </span>
                    </>
                  )}
                  {dias !== null && (
                    <span className={`priority-card__prazo ${urgente ? 'priority-card__prazo--urgente' : ''}`}>
                      {dias < 0 ? 'Encerrado' : dias === 0 ? 'Hoje' : `proposta em ${dias}d`}
                    </span>
                  )}
                </div>
                <p className="priority-card__objeto">{o.objeto_compra}</p>
                <p className="priority-card__meta">
                  {o.orgao_razao_social} · {getMunicipio(o)}
                </p>
                <p className="priority-card__foot">
                  {fmtMoney(o.valor_total_estimado)} · {o.modalidade || 'Pregão'} · pub. {fmtDate(o.data_publicacao)}
                </p>
                <p className="priority-card__why">{highlightReason(o, modo)}</p>
              </button>
            );
          })}
        </div>
      )}
    </section>
  );
}
