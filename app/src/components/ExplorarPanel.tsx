import { useCallback, useEffect, useState } from 'react';
import {
  fetchConcorrencia,
  fetchIndicadores,
  fetchOrgao,
  fetchOrgaos,
  fetchVisaoCategorias,
  fetchVisaoRegiao,
  saveOrgaoAnotacoes,
} from '../api';

export type ExplorarModo = 'orgaos' | 'categorias' | 'regioes' | 'indicadores' | 'concorrencia';

type Props = {
  modo: ExplorarModo;
  onSelectOportunidade: (numero: string) => void;
};

export function ExplorarPanel({ modo, onSelectOportunidade }: Props) {
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState('');
  const [orgaos, setOrgaos] = useState<Awaited<ReturnType<typeof fetchOrgaos>> | null>(null);
  const [detalhe, setDetalhe] = useState<Awaited<ReturnType<typeof fetchOrgao>> | null>(null);
  const [cats, setCats] = useState<Awaited<ReturnType<typeof fetchVisaoCategorias>> | null>(null);
  const [regs, setRegs] = useState<Awaited<ReturnType<typeof fetchVisaoRegiao>> | null>(null);
  const [inds, setInds] = useState<Awaited<ReturnType<typeof fetchIndicadores>> | null>(null);
  const [conc, setConc] = useState<Awaited<ReturnType<typeof fetchConcorrencia>> | null>(null);
  const [q, setQ] = useState('');
  const [anot, setAnot] = useState('');
  const [msg, setMsg] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setErro('');
    setDetalhe(null);
    try {
      if (modo === 'orgaos') setOrgaos(await fetchOrgaos({ q: q || undefined, limit: 100 }));
      if (modo === 'categorias') setCats(await fetchVisaoCategorias());
      if (modo === 'regioes') setRegs(await fetchVisaoRegiao());
      if (modo === 'indicadores') setInds(await fetchIndicadores());
      if (modo === 'concorrencia') setConc(await fetchConcorrencia());
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Erro ao carregar');
    } finally {
      setLoading(false);
    }
  }, [modo, q]);

  useEffect(() => {
    void load();
  }, [load]);

  async function abrirOrgao(chave: string) {
    setErro('');
    try {
      const d = await fetchOrgao(chave);
      setDetalhe(d);
      setAnot(d.anotacoes || '');
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Órgão não encontrado');
    }
  }

  async function salvarAnot() {
    if (!detalhe) return;
    try {
      await saveOrgaoAnotacoes(detalhe.orgao.orgao_chave, {
        anotacoes: anot,
        nome: detalhe.orgao.nome,
        cnpj: detalhe.orgao.cnpj,
      });
      setMsg('Anotação local guardada.');
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Falha ao salvar anotação');
    }
  }

  const titulo: Record<ExplorarModo, string> = {
    orgaos: 'Órgãos',
    categorias: 'Categorias / setores',
    regioes: 'Regiões (UF)',
    indicadores: 'Indicadores',
    concorrencia: 'Concorrência',
  };

  return (
    <section className="table-section">
      <header className="section-head">
        <div>
          <h2>{titulo[modo]}</h2>
          <p className="muted">Exploração a partir dos dados já coletados neste computador.</p>
        </div>
      </header>

      {loading && <p className="muted">Carregando…</p>}
      {erro && <p className="acomp__err">{erro}</p>}
      {msg && <p className="acomp__ok">{msg}</p>}

      {modo === 'orgaos' && orgaos && !detalhe && (
        <>
          <p className="coverage__aviso">{orgaos.aviso}</p>
          <ul className="muted">
            {orgaos.limitacoes.map((l) => (
              <li key={l}>{l}</li>
            ))}
          </ul>
          <div className="docs-analise__check-add">
            <input
              placeholder="Buscar órgão ou CNPJ"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && void load()}
            />
            <button type="button" className="btn btn--primary" onClick={() => void load()}>
              Buscar
            </button>
          </div>
          <p className="muted">{orgaos.total} órgão(s) no recorte</p>
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Órgão</th>
                  <th>UF</th>
                  <th>Oportunidades</th>
                  <th>Setores</th>
                  <th>Período</th>
                </tr>
              </thead>
              <tbody>
                {orgaos.items.map((o, idx) => (
                  <tr
                    key={o.orgao_chave}
                    className={idx % 2 ? 'data-table__row--zebra' : ''}
                    role="link"
                    tabIndex={0}
                    onClick={() => void abrirOrgao(o.orgao_chave)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        void abrirOrgao(o.orgao_chave);
                      }
                    }}
                  >
                    <td>
                      {o.nome}
                      {o.cnpj ? <div className="muted">{o.cnpj}</div> : null}
                    </td>
                    <td>{o.ufs.join(', ')}</td>
                    <td>{o.n_oportunidades}</td>
                    <td>{o.setores_observados.join(', ') || '—'}</td>
                    <td className="muted">
                      {(o.periodo_publicacao?.de || '—').slice(0, 10)} →{' '}
                      {(o.periodo_publicacao?.ate || '—').slice(0, 10)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {modo === 'orgaos' && detalhe && (
        <div className="docs-analise">
          <button type="button" className="btn btn--ghost" onClick={() => setDetalhe(null)}>
            ← Voltar à lista
          </button>
          <h3>{detalhe.orgao.nome}</h3>
          <p className="muted">
            {detalhe.orgao.cnpj || 'CNPJ não informado'} · UFs {detalhe.orgao.ufs.join(', ')} ·{' '}
            {detalhe.historico_disponivel.n_registros} registro(s)
          </p>
          <p className="drawer__hint">{detalhe.aviso}</p>
          <h4>Categorias observadas</h4>
          <ul>
            {detalhe.categorias_observadas.map((c) => (
              <li key={c.rotulo}>
                {c.rotulo}: {c.quantidade}
              </li>
            ))}
          </ul>
          <h4>Valores e período</h4>
          <p className="muted">
            Soma estimados (quando houver):{' '}
            {detalhe.orgao.valor_estimado_soma != null
              ? detalhe.orgao.valor_estimado_soma.toLocaleString('pt-BR')
              : 'Não informado'}
            <br />
            Publicações: {(detalhe.orgao.periodo_publicacao?.de || '—').slice(0, 10)} →{' '}
            {(detalhe.orgao.periodo_publicacao?.ate || '—').slice(0, 10)}
          </p>
          <h4>Anotações (locais)</h4>
          <textarea rows={3} value={anot} onChange={(e) => setAnot(e.target.value)} />
          <button type="button" className="btn btn--primary" onClick={() => void salvarAnot()}>
            Guardar anotação
          </button>
          <h4>Oportunidades relacionadas</h4>
          <ul className="docs-analise__list">
            {detalhe.oportunidades.map((o) => (
              <li key={o.numero_controle_pncp}>
                <button
                  type="button"
                  className="btn btn--ghost"
                  onClick={() => onSelectOportunidade(o.numero_controle_pncp)}
                >
                  {(o.objeto_compra || o.numero_controle_pncp).slice(0, 120)}
                </button>
                <span className="muted">
                  {o.uf} · {(o.data_publicacao || '').slice(0, 10)} · nicho legado {o.nicho_legado}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {modo === 'categorias' && cats && (
        <>
          <p className="coverage__aviso">{cats.aviso}</p>
          <ul className="muted">
            {cats.limitacoes.map((l) => (
              <li key={l}>{l}</li>
            ))}
          </ul>
          <table className="data-table">
            <thead>
              <tr>
                <th>Setor</th>
                <th>Categoria</th>
                <th>Qtd.</th>
              </tr>
            </thead>
            <tbody>
              {cats.items.map((c, i) => (
                <tr key={`${c.setor}-${c.categoria}`} className={i % 2 ? 'data-table__row--zebra' : ''}>
                  <td>{c.setor}</td>
                  <td>{c.categoria || '—'}</td>
                  <td>{c.quantidade}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}

      {modo === 'regioes' && regs && (
        <>
          <p className="coverage__aviso">{regs.aviso}</p>
          <ul className="muted">
            {regs.limitacoes.map((l) => (
              <li key={l}>{l}</li>
            ))}
          </ul>
          <table className="data-table">
            <thead>
              <tr>
                <th>UF</th>
                <th>Oportunidades</th>
                <th>Soma valores est.</th>
                <th>Período</th>
              </tr>
            </thead>
            <tbody>
              {regs.items.map((r, i) => (
                <tr key={r.uf} className={i % 2 ? 'data-table__row--zebra' : ''}>
                  <td>{r.uf}</td>
                  <td>{r.quantidade}</td>
                  <td>
                    {r.valor_estimado_soma != null
                      ? r.valor_estimado_soma.toLocaleString('pt-BR')
                      : '—'}
                  </td>
                  <td className="muted">
                    {(r.periodo_publicacao?.de || '—').slice(0, 10)} →{' '}
                    {(r.periodo_publicacao?.ate || '—').slice(0, 10)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}

      {modo === 'indicadores' && inds && (
        <div className="docs-analise">
          <p>
            <strong>Base de cálculo:</strong> {inds.base_calculo}
          </p>
          <p>
            <strong>Período:</strong> {(inds.periodo?.de || '—').slice(0, 10)} →{' '}
            {(inds.periodo?.ate || '—').slice(0, 10)}
          </p>
          <p>
            Total: {inds.total_oportunidades} · Com valor estimado: {inds.com_valor_estimado} (
            {inds.pct_com_valor_estimado}%)
          </p>
          <p className="coverage__aviso">{inds.aviso}</p>
          <h4>Limitações</h4>
          <ul>
            {inds.limitacoes.map((l) => (
              <li key={l}>{l}</li>
            ))}
          </ul>
          <h4>Top setores (classificação local)</h4>
          <ul>
            {inds.top_setores.map((s) => (
              <li key={`${s.setor}-${s.categoria}`}>
                {s.setor}/{s.categoria || '—'}: {s.quantidade}
              </li>
            ))}
          </ul>
        </div>
      )}

      {modo === 'concorrencia' && conc && (
        <div className="docs-analise">
          <h3>{conc.mensagem}</h3>
          {!conc.dados_suficientes && (
            <>
              <p>{conc.detalhe}</p>
              <p>
                <strong>Integração faltante:</strong> {conc.integracao_faltante}
              </p>
            </>
          )}
          <ul>
            {conc.limitacoes.map((l) => (
              <li key={l}>{l}</li>
            ))}
          </ul>
          <p className="muted">
            Oportunidades inspecionadas: {conc.oportunidades_inspecionadas}. Chaves de participantes
            encontradas: {conc.chaves_relevantes_encontradas.length ? conc.chaves_relevantes_encontradas.join(', ') : 'nenhuma'}.
          </p>
        </div>
      )}
    </section>
  );
}
