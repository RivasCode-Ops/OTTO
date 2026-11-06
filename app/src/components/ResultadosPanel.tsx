import { useEffect, useState } from 'react';
import { fetchResultados, fmtMoney } from '../api';
import type { Oportunidade } from '../types';

type Props = {
  onSelect: (o: Oportunidade) => void;
};

type Item = {
  oportunidade: Oportunidade;
  estado_fluxo: string;
  resultado_disputa: string;
  resultado_contratacao: string;
  resultado_execucao: string;
  resultado_recebimento: string;
  tempo_preparacao_horas: number | null;
  custo_preparacao: number | null;
};

export function ResultadosPanel({ onSelect }: Props) {
  const [items, setItems] = useState<Item[]>([]);
  const [aviso, setAviso] = useState('');
  const [erro, setErro] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    void (async () => {
      setLoading(true);
      setErro('');
      try {
        const data = await fetchResultados();
        setItems(data.items);
        setAviso(data.aviso);
      } catch (e) {
        setErro(e instanceof Error ? e.message : 'Falha ao carregar resultados');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <section className="table-section">
      <header className="section-head">
        <div>
          <h2>Resultados</h2>
          <p className="muted">{aviso}</p>
        </div>
      </header>
      {loading && <p className="muted">Carregando…</p>}
      {erro && <p className="acomp__err">{erro}</p>}
      {!loading && items.length === 0 && (
        <p className="muted">
          Nenhum resultado registrado ainda. No detalhe, use Preparação/Financeiro para marcar
          disputa/contratação/execução/recebimento ou tempo/custo de preparação.
        </p>
      )}
      {items.length > 0 && (
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Objeto</th>
                <th>Órgão</th>
                <th>Fluxo</th>
                <th>Disputa</th>
                <th>Contratação</th>
                <th>Execução</th>
                <th>Recebimento</th>
                <th className="data-table__num">Prep. (h)</th>
                <th className="data-table__num">Custo prep.</th>
              </tr>
            </thead>
            <tbody>
              {items.map((x, idx) => (
                <tr
                  key={x.oportunidade.numero_controle_pncp}
                  className={idx % 2 ? 'data-table__row--zebra' : ''}
                  onClick={() => onSelect(x.oportunidade)}
                >
                  <td className="data-table__objeto">{x.oportunidade.objeto_compra}</td>
                  <td>{x.oportunidade.orgao_razao_social || '—'}</td>
                  <td>{x.estado_fluxo}</td>
                  <td>{x.resultado_disputa}</td>
                  <td>{x.resultado_contratacao}</td>
                  <td>{x.resultado_execucao}</td>
                  <td>{x.resultado_recebimento}</td>
                  <td className="data-table__num">{x.tempo_preparacao_horas ?? '—'}</td>
                  <td className="data-table__num">{fmtMoney(x.custo_preparacao)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
