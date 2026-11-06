import type { KeyboardEvent } from 'react';
import { EmptyState } from './EmptyState';
import { fmtDate, fmtMoney } from '../api';
import type { Oportunidade } from '../types';
import { daysUntil, getMunicipio, labelCategoria, scoreTier } from '../utils';

type Props = {
  items: Oportunidade[];
  totalBase: number;
  modo: 'geral' | 'ti';
  somenteAlta: boolean;
  onSomenteAlta: (v: boolean) => void;
  onSelect: (o: Oportunidade) => void;
  selected?: string | null;
  loading: boolean;
  busca: string;
  ordenacaoRotulo: string;
};

export function OportunidadesTable({
  items,
  totalBase,
  modo,
  somenteAlta,
  onSomenteAlta,
  onSelect,
  selected,
  loading,
  busca,
  ordenacaoRotulo,
}: Props) {
  const geral = modo === 'geral';

  function onRowKey(e: KeyboardEvent<HTMLTableRowElement>, o: Oportunidade) {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onSelect(o);
    }
  }

  return (
    <section className="table-section">
      <header className="section-head">
        <div>
          <h2>Explorar oportunidades</h2>
          <p className="muted">
            {items.length} registro(s) no recorte · ordenação: {ordenacaoRotulo}
          </p>
        </div>
        {modo === 'ti' && (
          <label className="toggle">
            <input
              type="checkbox"
              checked={somenteAlta}
              onChange={(e) => onSomenteAlta(e.target.checked)}
            />
            Somente alta confiança (TI)
          </label>
        )}
      </header>

      {!loading && items.length === 0 ? (
        <EmptyState
          title={totalBase === 0 ? 'Nenhum edital no banco' : 'Filtro sem resultados'}
          hint={
            totalBase === 0
              ? 'Rode otto ingest --days 7 e recarregue o painel.'
              : busca
                ? `Nada encontrado para “${busca}”. Limpe a busca ou ajuste o período.`
                : modo === 'ti'
                  ? 'Desmarque “somente alta confiança” ou amplie o período / volte à lista geral.'
                  : 'Amplie o filtro de prazo ou limpe a busca.'
          }
        />
      ) : (
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                {geral ? (
                  <>
                    <th>Publicação</th>
                    <th>Categoria</th>
                  </>
                ) : (
                  <>
                    <th className="data-table__num">Score</th>
                    <th>Conf.</th>
                  </>
                )}
                <th>Objeto</th>
                <th>Órgão</th>
                <th>Município</th>
                <th className="data-table__num">Valor</th>
                <th className="data-table__num">Prazo proposta</th>
                <th>Docs</th>
                <th>Esclar.</th>
                <th>Impug.</th>
                <th>Origem</th>
                <th>Situação</th>
              </tr>
            </thead>
            <tbody>
              {items.map((o, idx) => {
                const tier = scoreTier(o.score_total);
                const dias = daysUntil(o.data_encerramento);
                const categoria = labelCategoria(o);
                const docs = o.documentos_count ?? 0;
                return (
                  <tr
                    key={o.numero_controle_pncp}
                    className={`${idx % 2 === 1 ? 'data-table__row--zebra' : ''} ${selected === o.numero_controle_pncp ? 'data-table__row--selected' : ''}`}
                    onClick={() => onSelect(o)}
                    onKeyDown={(e) => onRowKey(e, o)}
                    tabIndex={0}
                    role="button"
                    aria-label={`Abrir detalhe: ${o.objeto_compra}`}
                  >
                    {geral ? (
                      <>
                        <td>{fmtDate(o.data_publicacao)}</td>
                        <td>{categoria}</td>
                      </>
                    ) : (
                      <>
                        <td className="data-table__num">
                          <span className={`score-badge score-badge--${tier}`}>{o.score_total.toFixed(1)}</span>
                        </td>
                        <td>
                          <span className={`conf-pill conf-pill--${o.confianca_classificacao}`}>
                            {o.confianca_classificacao === 'alta' ? 'alta' : 'baixa'}
                          </span>
                        </td>
                      </>
                    )}
                    <td className="data-table__objeto">{o.objeto_compra}</td>
                    <td>{o.orgao_razao_social}</td>
                    <td>{getMunicipio(o)}</td>
                    <td className="data-table__num">{fmtMoney(o.valor_total_estimado)}</td>
                    <td className="data-table__num">
                      {fmtDate(o.data_encerramento)}
                      {dias !== null && dias >= 0 && (
                        <span className={`data-table__dias ${dias <= 7 ? 'data-table__dias--urgente' : ''}`}>
                          {dias}d
                        </span>
                      )}
                    </td>
                    <td className="data-table__num" title="Documentos anexados neste computador">
                      {docs > 0 ? docs : '—'}
                    </td>
                    <td title="Prazo de esclarecimento">{fmtDate(o.data_esclarecimento)}</td>
                    <td title="Prazo de impugnação">{fmtDate(o.data_impugnacao)}</td>
                    <td>{o.origem_registro === 'manual' ? 'manual' : 'PNCP'}</td>
                    <td>{o.situacao}</td>
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
