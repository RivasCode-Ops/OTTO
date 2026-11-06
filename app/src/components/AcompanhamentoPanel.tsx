import { fmtDate, fmtMoney } from '../api';
import type { Acompanhamento, Oportunidade } from '../types';
import { EmptyState } from './EmptyState';
import { getMunicipio } from '../utils';

type Item = { oportunidade: Oportunidade; acompanhamento: Acompanhamento };

type Props = {
  titulo: string;
  descricao: string;
  aviso?: string;
  items: Item[];
  loading: boolean;
  onSelect: (o: Oportunidade) => void;
  selected?: string | null;
};

export function AcompanhamentoPanel({
  titulo,
  descricao,
  aviso,
  items,
  loading,
  onSelect,
  selected,
}: Props) {
  return (
    <section className="table-section">
      <header className="section-head">
        <div>
          <h2>{titulo}</h2>
          <p className="muted">{descricao}</p>
          {aviso && <p className="coverage__aviso" style={{ marginTop: '0.5rem' }}>{aviso}</p>}
        </div>
      </header>

      {!loading && items.length === 0 ? (
        <EmptyState
          title="Nenhuma oportunidade neste recorte"
          hint="Abra a lista geral, escolha um item e use Salvar / Interesse / Decisão no detalhe."
        />
      ) : (
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Atualizado</th>
                <th>Estado</th>
                <th>Objeto</th>
                <th>Órgão</th>
                <th>Local</th>
                <th className="data-table__num">Valor est.</th>
              </tr>
            </thead>
            <tbody>
              {items.map((row, idx) => {
                const o = row.oportunidade;
                const a = row.acompanhamento;
                const flags = [
                  a.salva ? 'salva' : null,
                  a.interesse ? 'interesse' : null,
                  a.decisao !== 'sem_decisao' ? a.decisao.replace('_', ' ') : null,
                ]
                  .filter(Boolean)
                  .join(' · ');
                return (
                  <tr
                    key={o.numero_controle_pncp}
                    className={`${idx % 2 === 1 ? 'data-table__row--zebra' : ''} ${selected === o.numero_controle_pncp ? 'data-table__row--selected' : ''}`}
                    onClick={() => onSelect(o)}
                  >
                    <td>{fmtDate(a.atualizado_em)}</td>
                    <td>{flags || '—'}</td>
                    <td className="data-table__objeto">{o.objeto_compra}</td>
                    <td>{o.orgao_razao_social}</td>
                    <td>
                      {getMunicipio(o)} · {o.uf}
                    </td>
                    <td className="data-table__num">{fmtMoney(o.valor_total_estimado)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
