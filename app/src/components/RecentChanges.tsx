import type { EventoRecente } from '../types';
import { fmtDate } from '../api';

type Props = {
  total: number;
  items: EventoRecente[];
  loading?: boolean;
  onSelect?: (numero: string) => void;
};

function labelCampo(campo: string): string {
  const map: Record<string, string> = {
    situacao: 'Situação',
    valor_total_estimado: 'Valor',
    data_encerramento: 'Prazo',
  };
  return map[campo] ?? campo;
}

export function RecentChanges({ total, items, loading, onSelect }: Props) {
  return (
    <section className="recent" aria-label="Mudanças recentes">
      <header className="section-head">
        <div>
          <h2>Mudanças recentes</h2>
          <p className="muted">Alterações de prazo, situação ou valor nos últimos 7 dias</p>
        </div>
        {!loading && (
          <span className={`recent__count ${total > 0 ? 'recent__count--active' : ''}`}>{total}</span>
        )}
      </header>

      {loading ? (
        <div className="recent__list">
          {[1, 2, 3].map((i) => (
            <div key={i} className="recent-item skeleton-block" />
          ))}
        </div>
      ) : items.length === 0 ? (
        <div className="empty-state empty-state--compact">
          <p className="empty-state__title">Nenhuma mudança registrada</p>
          <p className="muted">
            Quando o PNCP alterar prazo ou situação, o histórico aparece aqui após a próxima coleta.
          </p>
        </div>
      ) : (
        <div className="recent__list">
          {items.map((e) => (
            <button
              key={e.id}
              type="button"
              className="recent-item"
              onClick={() => onSelect?.(e.numero_controle_pncp)}
            >
              <span className="recent-item__tag">{labelCampo(e.campo)}</span>
              <p className="recent-item__orgao">{e.orgao_razao_social}</p>
              <p className="recent-item__change">
                {e.valor_anterior ?? '—'} → {e.valor_novo ?? '—'}
              </p>
              <time className="recent-item__time">{fmtDate(e.detectado_em)}</time>
            </button>
          ))}
        </div>
      )}
    </section>
  );
}
