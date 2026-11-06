import { useCallback, useEffect, useState } from 'react';
import {
  checklistFromRequisito,
  createRequisito,
  documentoArquivoUrl,
  fetchAnalise,
  fetchDocumentoPaginas,
  fetchRequisitos,
  gerarRequisitosDaFicha,
  patchRequisito,
  type RequisitoItem,
} from '../api';
import type { DocumentoMeta } from '../types';

type Props = { numero: string };

const ESTADOS: { value: string; label: string }[] = [
  { value: 'nao_avaliado', label: 'Não avaliado' },
  { value: 'evidencia_cadastrada', label: 'Evidência cadastrada' },
  { value: 'declaracao_usuario', label: 'Declaração do usuário' },
  { value: 'pendente_confirmacao', label: 'Pendente de confirmação' },
  { value: 'nao_atendido', label: 'Não atendido' },
];

function paginaAplicavel(doc: DocumentoMeta | undefined, meta?: RequisitoItem['evidencia_documento']) {
  if (meta && typeof meta.pagina_aplicavel === 'boolean') return meta.pagina_aplicavel;
  if (!doc) return true;
  return !String(doc.tipo_mime || '').startsWith('text/');
}

export function RequisitosPanel({ numero }: Props) {
  const [items, setItems] = useState<RequisitoItem[]>([]);
  const [docs, setDocs] = useState<DocumentoMeta[]>([]);
  const [aviso, setAviso] = useState('');
  const [novo, setNovo] = useState('');
  const [erro, setErro] = useState('');
  const [msg, setMsg] = useState('');
  const [drafts, setDrafts] = useState<
    Record<number, { pagina: string; trecho: string }>
  >({});
  const [localizando, setLocalizando] = useState<{
    reqId: number;
    nome: string;
    pagina: number | null;
    trecho: string;
    pags: { pagina: number; texto: string }[];
  } | null>(null);

  const reload = useCallback(async () => {
    setErro('');
    try {
      const data = await fetchRequisitos(numero);
      setItems(data.items);
      setAviso(data.aviso);
      const next: Record<number, { pagina: string; trecho: string }> = {};
      for (const r of data.items) {
        next[r.id] = {
          pagina: r.evidencia_pagina != null ? String(r.evidencia_pagina) : '',
          trecho: r.evidencia_trecho || '',
        };
      }
      setDrafts(next);
      try {
        const d = await fetchAnalise(numero);
        setDocs(d.documentos);
      } catch {
        setDocs([]);
      }
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Falha nos requisitos');
    }
  }, [numero]);

  useEffect(() => {
    void reload();
  }, [reload]);

  async function add() {
    const t = novo.trim();
    if (!t) return;
    try {
      const data = await createRequisito(numero, { descricao: t });
      setItems(data.items as RequisitoItem[]);
      setNovo('');
      setAviso(data.aviso);
      await reload();
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Falha ao incluir');
    }
  }

  async function setEstado(id: number, estado: string) {
    try {
      const data = await patchRequisito(numero, id, { estado });
      setItems(data.items);
      setAviso(data.aviso);
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Falha ao atualizar');
    }
  }

  async function salvarEvidencia(r: RequisitoItem) {
    const draft = drafts[r.id] || { pagina: '', trecho: '' };
    const doc = docs.find((d) => d.id === r.evidencia_documento_id);
    const comPagina = paginaAplicavel(doc, r.evidencia_documento);
    const pagTrim = draft.pagina.trim();
    try {
      const data = await patchRequisito(numero, r.id, {
        evidencia_trecho: draft.trecho,
        evidencia_pagina: comPagina && pagTrim ? Number(pagTrim) : null,
        limpar_evidencia_pagina: !comPagina || !pagTrim,
        estado: r.evidencia_documento_id ? 'evidencia_cadastrada' : undefined,
        confirmar_revisao_usuario: Boolean(r.precisa_revisao),
      });
      setItems(data.items);
      setMsg(`Evidência do requisito “${r.descricao}” guardada (versão do documento preservada).`);
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Falha na evidência');
    }
  }

  async function setEvidenciaDoc(id: number, docId: string) {
    try {
      const data = await patchRequisito(numero, id, {
        evidencia_documento_id: docId ? Number(docId) : null,
        limpar_evidencia_doc: !docId,
        limpar_evidencia_pagina: !docId,
        estado: docId ? 'evidencia_cadastrada' : undefined,
      });
      setItems(data.items);
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Falha na evidência');
    }
  }

  async function gerarDaFicha() {
    setMsg('');
    try {
      const data = await gerarRequisitosDaFicha(numero);
      setItems(data.items as RequisitoItem[]);
      setAviso(data.aviso);
      setMsg(`Gerados ${data.gerados ?? 0} requisito(s) a partir da ficha.`);
      await reload();
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Falha ao gerar da ficha');
    }
  }

  async function criarTarefa(r: RequisitoItem) {
    try {
      await checklistFromRequisito(numero, r.id);
      setMsg(`Tarefa criada a partir do requisito “${r.descricao}”.`);
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Falha ao criar tarefa');
    }
  }

  async function localizarEvidencia(r: RequisitoItem) {
    if (!r.evidencia_documento_id) {
      setErro('Este requisito ainda não tem documento vinculado.');
      return;
    }
    setErro('');
    try {
      const meta = docs.find((d) => d.id === r.evidencia_documento_id);
      const pags = await fetchDocumentoPaginas(numero, r.evidencia_documento_id);
      setLocalizando({
        reqId: r.id,
        nome: meta?.nome_original || r.evidencia_documento?.nome_original || `doc #${r.evidencia_documento_id}`,
        pagina: r.evidencia_pagina ?? null,
        trecho: r.evidencia_trecho || '',
        pags: pags.paginas,
      });
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Falha ao abrir evidência');
    }
  }

  return (
    <section className="drawer__block" id="requisitos-verificacao">
      <h3>Verificação de requisitos (§9.2)</h3>
      <p className="drawer__hint">{aviso}</p>
      <div className="docs-analise__check-add">
        <input
          value={novo}
          onChange={(e) => setNovo(e.target.value)}
          placeholder="Ex.: Certidão federal negativa"
          onKeyDown={(e) => e.key === 'Enter' && void add()}
        />
        <button type="button" className="btn btn--primary" onClick={() => void add()}>
          Incluir requisito
        </button>
        <button type="button" className="btn btn--ghost" onClick={() => void gerarDaFicha()}>
          Gerar a partir da ficha
        </button>
      </div>
      <ul className="docs-analise__list">
        {items.map((r) => {
          const doc = docs.find((d) => d.id === r.evidencia_documento_id);
          const comPagina = paginaAplicavel(doc, r.evidencia_documento);
          const draft = drafts[r.id] || { pagina: '', trecho: '' };
          return (
            <li key={r.id}>
              <div>
                <strong>{r.descricao}</strong>
                {r.origem ? <p className="muted">Origem: {r.origem}</p> : null}
                {r.precisa_revisao ? (
                  <p className="acomp__err">
                    Revisar evidência (nova versão do documento). Vínculo antigo preservado
                    {r.evidencia_documento_id ? ` · doc #${r.evidencia_documento_id}` : ''}
                    {r.evidencia_documento
                      ? ` · v${r.evidencia_documento.versao} · ${r.evidencia_documento.nome_original}`
                      : ''}
                    .
                  </p>
                ) : null}
                {r.revisao_origem === 'usuario' && !r.precisa_revisao ? (
                  <p className="muted">Revisão confirmada por você (não automática).</p>
                ) : null}
                {r.observacao ? <p className="muted">{r.observacao}</p> : null}
                <label className="acomp__label">
                  Evidência (versão do documento)
                  <select
                    value={r.evidencia_documento_id ?? ''}
                    aria-label={`Evidência de ${r.descricao}`}
                    onChange={(e) => void setEvidenciaDoc(r.id, e.target.value)}
                  >
                    <option value="">Sem documento vinculado</option>
                    {docs.map((d) => (
                      <option key={d.id} value={d.id}>
                        #{d.id} {d.nome_original} (v{d.versao})
                      </option>
                    ))}
                  </select>
                </label>
                <div className="docs-analise__check-add">
                  {comPagina ? (
                    <input
                      placeholder="Página (opcional)"
                      aria-label={`Página evidência ${r.descricao}`}
                      value={draft.pagina}
                      onChange={(e) =>
                        setDrafts((d) => ({
                          ...d,
                          [r.id]: { pagina: e.target.value, trecho: d[r.id]?.trecho ?? '' },
                        }))
                      }
                    />
                  ) : (
                    <span className="muted">Sem número de página (TXT / texto contínuo)</span>
                  )}
                  <input
                    placeholder="Trecho de origem"
                    aria-label={`Trecho evidência ${r.descricao}`}
                    value={draft.trecho}
                    onChange={(e) =>
                      setDrafts((d) => ({
                        ...d,
                        [r.id]: { pagina: d[r.id]?.pagina ?? '', trecho: e.target.value },
                      }))
                    }
                  />
                </div>
                <div className="docs-analise__doc-actions">
                  <button
                    type="button"
                    className="btn btn--ghost"
                    onClick={() => void salvarEvidencia(r)}
                  >
                    Guardar evidência
                  </button>
                  {r.evidencia_documento_id ? (
                    <>
                      <a
                        className="btn btn--ghost"
                        href={documentoArquivoUrl(numero, r.evidencia_documento_id)}
                        target="_blank"
                        rel="noreferrer"
                      >
                        Abrir documento
                      </a>
                      <button
                        type="button"
                        className="btn btn--ghost"
                        onClick={() => void localizarEvidencia(r)}
                      >
                        Localizar referência
                      </button>
                    </>
                  ) : null}
                  <button
                    type="button"
                    className="btn btn--ghost"
                    onClick={() => void criarTarefa(r)}
                  >
                    Criar tarefa
                  </button>
                  {r.precisa_revisao ? (
                    <button
                      type="button"
                      className="btn btn--primary"
                      onClick={() =>
                        void patchRequisito(numero, r.id, { confirmar_revisao_usuario: true })
                          .then((data) => {
                            setItems(data.items);
                            setMsg('Revisão do requisito confirmada por você.');
                          })
                          .catch((e) =>
                            setErro(e instanceof Error ? e.message : 'Falha ao confirmar'),
                          )
                      }
                    >
                      Confirmei a revisão
                    </button>
                  ) : null}
                </div>
                {r.evidencia_documento_id ? (
                  <p className="drawer__hint">
                    Referência: doc #{r.evidencia_documento_id}
                    {r.evidencia_documento ? ` · v${r.evidencia_documento.versao}` : ''}
                    {r.evidencia_pagina != null
                      ? ` · página ${r.evidencia_pagina}`
                      : comPagina
                        ? ' · página não informada'
                        : ' · sem página (TXT)'}
                    {r.evidencia_trecho ? ` · trecho: “${r.evidencia_trecho.slice(0, 80)}”` : ''}
                  </p>
                ) : null}
              </div>
              <select
                value={r.estado}
                aria-label={`Estado de ${r.descricao}`}
                onChange={(e) => void setEstado(r.id, e.target.value)}
              >
                {ESTADOS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </li>
          );
        })}
      </ul>
      {localizando && (
        <div className="docs-analise__pages">
          <header>
            <strong>
              Evidência: {localizando.nome}
              {localizando.pagina != null
                ? ` — página ${localizando.pagina}`
                : ' — sem número de página'}
            </strong>
            <button type="button" className="btn btn--ghost" onClick={() => setLocalizando(null)}>
              Fechar
            </button>
          </header>
          {localizando.trecho ? (
            <p className="drawer__hint">Trecho cadastrado: “{localizando.trecho}”</p>
          ) : null}
          {localizando.pagina != null && !localizando.pags.some((p) => p.pagina === localizando.pagina) ? (
            <p className="acomp__err">
              Página {localizando.pagina} registrada na evidência; navegação direta indisponível —
              abra o documento e vá até essa página.
            </p>
          ) : null}
          {localizando.pags.length === 0 ? (
            <p className="muted">Sem texto extraído para localizar.</p>
          ) : (
            localizando.pags.map((p) => {
              const alvo = localizando.pagina != null && p.pagina === localizando.pagina;
              const trecho = localizando.trecho.trim().toLowerCase();
              const temTrecho = trecho && p.texto.toLowerCase().includes(trecho);
              return (
                <article
                  key={p.pagina}
                  style={
                    alvo || temTrecho
                      ? { outline: '2px solid var(--accent, #2563eb)', padding: '0.5rem' }
                      : undefined
                  }
                >
                  <h4>
                    Página {p.pagina}
                    {alvo ? ' (referência da evidência)' : ''}
                    {temTrecho && !alvo ? ' (trecho encontrado)' : ''}
                  </h4>
                  <pre>{p.texto.trim() || '(sem texto nesta página)'}</pre>
                </article>
              );
            })
          )}
        </div>
      )}
      {msg && <p className="acomp__ok">{msg}</p>}
      {erro && <p className="acomp__err">{erro}</p>}
    </section>
  );
}
