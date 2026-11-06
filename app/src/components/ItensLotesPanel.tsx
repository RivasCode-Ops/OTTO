import { useCallback, useEffect, useState } from 'react';
import { createItem, createLote, fetchItensLotes, patchItem, patchLote } from '../api';

type Props = { numero: string };

type Item = {
  id: number;
  lote_id: number | null;
  descricao: string;
  quantidade: number | null;
  unidade: string;
  setor?: string;
  categoria?: string;
  setor_sugerido?: string;
  categoria_sugerida?: string;
  classificacao_origem?: string;
};

export function ItensLotesPanel({ numero }: Props) {
  const [lotes, setLotes] = useState<
    { id: number; codigo: string; descricao: string; disputa_separada_confirmada: boolean }[]
  >([]);
  const [itens, setItens] = useState<Item[]>([]);
  const [aviso, setAviso] = useState('');
  const [loteDesc, setLoteDesc] = useState('');
  const [itemDesc, setItemDesc] = useState('');
  const [itemLote, setItemLote] = useState('');
  const [itemSetor, setItemSetor] = useState('');
  const [itemCat, setItemCat] = useState('');
  const [erro, setErro] = useState('');

  const reload = useCallback(async () => {
    setErro('');
    try {
      const data = await fetchItensLotes(numero);
      setLotes(data.lotes);
      setItens(data.itens as Item[]);
      setAviso(data.aviso);
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Falha itens/lotes');
    }
  }, [numero]);

  useEffect(() => {
    void reload();
  }, [reload]);

  return (
    <section className="drawer__block">
      <h3>Itens e lotes</h3>
      <p className="drawer__hint">{aviso}</p>
      <div className="docs-analise__check-add">
        <input
          value={loteDesc}
          onChange={(e) => setLoteDesc(e.target.value)}
          placeholder="Descrição do lote"
        />
        <button
          type="button"
          className="btn btn--primary"
          onClick={() =>
            void createLote(numero, { descricao: loteDesc }).then((d) => {
              setLotes(d.lotes);
              setItens(d.itens as Item[]);
              setLoteDesc('');
            })
          }
        >
          Incluir lote
        </button>
      </div>
      <ul className="docs-analise__list">
        {lotes.map((l) => (
          <li key={l.id}>
            <div>
              <strong>
                Lote #{l.id}
                {l.codigo ? ` (${l.codigo})` : ''}: {l.descricao || '—'}
              </strong>
              <label className="acomp__label">
                <input
                  type="checkbox"
                  checked={l.disputa_separada_confirmada}
                  onChange={(e) =>
                    void patchLote(numero, l.id, {
                      disputa_separada_confirmada: e.target.checked,
                    }).then((d) => {
                      setLotes(d.lotes);
                      setItens(d.itens as Item[]);
                    })
                  }
                />{' '}
                Documentos confirmam disputa separada deste lote
              </label>
            </div>
          </li>
        ))}
      </ul>
      <div className="docs-analise__check-add">
        <input
          value={itemDesc}
          onChange={(e) => setItemDesc(e.target.value)}
          placeholder="Descrição do item"
        />
        <select value={itemLote} onChange={(e) => setItemLote(e.target.value)} aria-label="Lote do item">
          <option value="">Sem lote</option>
          {lotes.map((l) => (
            <option key={l.id} value={String(l.id)}>
              Lote #{l.id}
            </option>
          ))}
        </select>
        <input
          value={itemSetor}
          onChange={(e) => setItemSetor(e.target.value)}
          placeholder="Setor (manual, opcional)"
          aria-label="Setor do item"
        />
        <input
          value={itemCat}
          onChange={(e) => setItemCat(e.target.value)}
          placeholder="Categoria (manual, opcional)"
          aria-label="Categoria do item"
        />
        <button
          type="button"
          className="btn btn--primary"
          onClick={() =>
            void createItem(numero, {
              descricao: itemDesc,
              lote_id: itemLote ? Number(itemLote) : null,
              setor: itemSetor || undefined,
              categoria: itemCat || undefined,
            }).then((d) => {
              setLotes(d.lotes);
              setItens(d.itens as Item[]);
              setItemDesc('');
              setItemSetor('');
              setItemCat('');
            })
          }
        >
          Incluir item
        </button>
      </div>
      <ul className="docs-analise__list">
        {itens.map((i) => (
          <li key={i.id}>
            <div>
              <strong>{i.descricao}</strong>
              <span className="muted">
                {i.lote_id != null ? ` · lote #${i.lote_id}` : ' · sem lote'}
                {i.quantidade != null ? ` · qtd ${i.quantidade}` : ''}
                {i.unidade ? ` ${i.unidade}` : ''}
              </span>
              <p className="muted">
                Classificação atual: {i.setor || '—'} / {i.categoria || '—'}
                {i.classificacao_origem
                  ? ` (origem: ${i.classificacao_origem})`
                  : ' (sem classificação do usuário)'}
              </p>
              {i.setor_sugerido ? (
                <p className="drawer__hint">
                  Sugestão determinística (não aplicada): {i.setor_sugerido}
                  {i.categoria_sugerida && i.categoria_sugerida !== i.setor_sugerido
                    ? ` / ${i.categoria_sugerida}`
                    : ''}
                  .{' '}
                  <button
                    type="button"
                    className="btn btn--ghost"
                    onClick={() =>
                      void patchItem(numero, i.id, {
                        setor: i.setor_sugerido || '',
                        categoria: i.categoria_sugerida || i.setor_sugerido || '',
                      }).then((d) => {
                        setLotes(d.lotes);
                        setItens(d.itens as Item[]);
                      })
                    }
                  >
                    Aceitar sugestão
                  </button>
                </p>
              ) : null}
              <label className="acomp__label">
                Setor (manual)
                <input
                  defaultValue={i.setor || ''}
                  key={`setor-${i.id}-${i.setor || ''}`}
                  onBlur={(e) => {
                    const v = e.target.value.trim();
                    if (v === (i.setor || '')) return;
                    void patchItem(numero, i.id, { setor: v }).then((d) => {
                      setLotes(d.lotes);
                      setItens(d.itens as Item[]);
                    });
                  }}
                />
              </label>
              <label className="acomp__label">
                Categoria (manual)
                <input
                  defaultValue={i.categoria || ''}
                  key={`cat-${i.id}-${i.categoria || ''}`}
                  onBlur={(e) => {
                    const v = e.target.value.trim();
                    if (v === (i.categoria || '')) return;
                    void patchItem(numero, i.id, { categoria: v }).then((d) => {
                      setLotes(d.lotes);
                      setItens(d.itens as Item[]);
                    });
                  }}
                />
              </label>
            </div>
          </li>
        ))}
      </ul>
      {erro && <p className="acomp__err">{erro}</p>}
    </section>
  );
}
