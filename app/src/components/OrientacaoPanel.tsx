import { useCallback, useEffect, useState } from 'react';
import { fetchOrientacao, saveOrientacao } from '../api';

type Props = { numero: string };

const OPCOES: { value: string; label: string }[] = [
  { value: 'sim', label: 'Sim' },
  { value: 'nao', label: 'Não' },
  { value: 'nao_sei', label: 'Não sei' },
  { value: 'preciso_verificar', label: 'Preciso verificar' },
  { value: 'nao_respondida', label: 'Ainda não respondi' },
];

export function OrientacaoPanel({ numero }: Props) {
  const [items, setItems] = useState<
    { id: string; texto: string; resposta: string; detalhe: string }[]
  >([]);
  const [aviso, setAviso] = useState('');
  const [erro, setErro] = useState('');

  const reload = useCallback(async () => {
    setErro('');
    try {
      const data = await fetchOrientacao(numero);
      setItems(data.items);
      setAviso(data.aviso);
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Falha na orientação');
    }
  }, [numero]);

  useEffect(() => {
    void reload();
  }, [reload]);

  async function onResposta(id: string, resposta: string) {
    try {
      const data = await saveOrientacao(numero, id, { resposta });
      setItems(data.items);
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Falha ao guardar resposta');
    }
  }

  return (
    <section className="drawer__block" id="orientacao-participacao">
      <h3>Orientação para participação (perguntas)</h3>
      <p className="drawer__hint">{aviso}</p>
      <ul className="docs-analise__list">
        {items.map((q) => (
          <li key={q.id}>
            <div>
              <strong>{q.texto}</strong>
              <select
                value={q.resposta}
                aria-label={q.texto}
                onChange={(e) => void onResposta(q.id, e.target.value)}
              >
                {OPCOES.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </div>
          </li>
        ))}
      </ul>
      {erro && <p className="acomp__err">{erro}</p>}
    </section>
  );
}
