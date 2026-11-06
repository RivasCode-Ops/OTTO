import { useEffect, useState } from 'react';
import { addClassificacao, fetchClassificacoes } from '../api';

type Props = { numero: string };

export function ClassificacaoPanel({ numero }: Props) {
  const [items, setItems] = useState<{ setor: string; categoria: string; origem: string }[]>([]);
  const [setor, setSetor] = useState('saude');
  const [categoria, setCategoria] = useState('');
  const [erro, setErro] = useState('');

  async function reload() {
    const r = await fetchClassificacoes(numero);
    setItems(r.items);
  }

  useEffect(() => {
    void fetchClassificacoes(numero)
      .then((r) => setItems(r.items))
      .catch((e) => setErro(e instanceof Error ? e.message : 'Erro'));
  }, [numero]);

  async function add() {
    setErro('');
    try {
      await addClassificacao(numero, { setor, categoria });
      setCategoria('');
      await reload();
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Falha');
    }
  }

  return (
    <section className="drawer__block">
      <h3>Classificação multissetorial</h3>
      <p className="drawer__hint">
        Várias classificações por oportunidade. Não restringe a lista geral a TI. Revisões manuais
        ficam com origem “usuario”.
      </p>
      <ul>
        {items.map((i, idx) => (
          <li key={`${i.setor}-${i.categoria}-${idx}`}>
            {i.setor} / {i.categoria || '—'} <span className="muted">({i.origem})</span>
          </li>
        ))}
      </ul>
      <div className="docs-analise__check-add">
        <select value={setor} onChange={(e) => setSetor(e.target.value)} aria-label="Setor">
          <option value="ti">ti</option>
          <option value="saude">saude</option>
          <option value="limpeza">limpeza</option>
          <option value="obras">obras</option>
          <option value="mobiliario">mobiliario</option>
          <option value="alimentacao">alimentacao</option>
          <option value="outros">outros</option>
        </select>
        <input
          placeholder="Categoria (opcional)"
          value={categoria}
          onChange={(e) => setCategoria(e.target.value)}
        />
        <button type="button" className="btn btn--ghost" onClick={() => void add()}>
          Incluir
        </button>
      </div>
      {erro && <p className="acomp__err">{erro}</p>}
    </section>
  );
}
