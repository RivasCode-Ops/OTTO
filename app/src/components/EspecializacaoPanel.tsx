import { useEffect, useState } from 'react';
import { fetchEspecializacao } from '../api';

type Props = { numero: string; nicho?: string | null };

export function EspecializacaoPanel({ numero, nicho }: Props) {
  const [data, setData] = useState<Awaited<ReturnType<typeof fetchEspecializacao>> | null>(null);
  const [erro, setErro] = useState('');

  useEffect(() => {
    let cancel = false;
    setErro('');
    void (async () => {
      try {
        const r = await fetchEspecializacao(numero);
        if (!cancel) setData(r);
      } catch (e) {
        if (!cancel) setErro(e instanceof Error ? e.message : 'Falha na especialização');
      }
    })();
    return () => {
      cancel = true;
    };
  }, [numero, nicho]);

  if (erro) {
    return (
      <section className="drawer__block">
        <h3>Especialização setorial</h3>
        <p className="erro">{erro}</p>
      </section>
    );
  }
  if (!data) {
    return (
      <section className="drawer__block">
        <h3>Especialização setorial</h3>
        <p className="muted">Carregando…</p>
      </section>
    );
  }
  if (!data.especializacao) {
    return null;
  }

  return (
    <section className="drawer__block">
      <h3>Especialização · {data.rotulo}</h3>
      <p className="drawer__hint">{data.aviso}</p>
      <p className="muted">Nicho: {data.nicho_rotulo || data.nicho}</p>

      <h4>Subtipos identificados no objeto</h4>
      {data.subtipos.length === 0 ? (
        <p className="muted">Nenhum subtipo identificado no texto do objeto.</p>
      ) : (
        <ul>
          {data.subtipos.map((s) => (
            <li key={s.id}>
              <strong>{s.rotulo}</strong>
              <span className="muted"> — sinais: {s.sinais.join(', ')}</span>
            </li>
          ))}
        </ul>
      )}

      <h4>Condições mencionadas no objeto</h4>
      {data.condicoes_mencionadas.length === 0 ? (
        <p className="muted">Nenhuma condição específica citada no objeto.</p>
      ) : (
        <ul>
          {data.condicoes_mencionadas.map((c) => (
            <li key={c.id}>
              <strong>{c.rotulo}</strong>
              <span className="muted"> — sinais: {c.sinais.join(', ')}</span>
            </li>
          ))}
        </ul>
      )}

      <ul className="muted">
        {data.limitacoes.map((l) => (
          <li key={l}>{l}</li>
        ))}
      </ul>
    </section>
  );
}
