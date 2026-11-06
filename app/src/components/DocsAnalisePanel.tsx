import { useCallback, useEffect, useState } from 'react';
import {
  checklistFromCampo,
  confirmarRevisaoFicha,
  createChecklistItem,
  documentoArquivoUrl,
  fetchAnalise,
  baixarAnexosRemotos,
  fetchAnexosRemotos,
  fetchDocumentoPaginas,
  patchChecklistItem,
  reprocessarDocumentoOcr,
  saveAnaliseCampo,
  uploadDocumento,
  type AnexoRemoto,
} from '../api';
import type { AnaliseCampo, AnaliseFicha, ChecklistItem, DocumentoMeta } from '../types';
import { IaAnalisePanel } from './IaAnalisePanel';

type Props = { numero: string };

const NATUREZA_LABEL: Record<string, string> = {
  coleta: 'Da coleta',
  extraido: 'Extraído do documento',
  interpretacao: 'Interpretação (não é transcrição)',
  estimativa: 'Estimativa',
  usuario: 'Preenchido / confirmado por você',
  nao_confirmado: 'Não confirmado',
  sugerido_ia: 'Sugestão da IA local (não confirmada)',
};

export function DocsAnalisePanel({ numero }: Props) {
  const [ficha, setFicha] = useState<AnaliseFicha | null>(null);
  const [docs, setDocs] = useState<DocumentoMeta[]>([]);
  const [checklist, setChecklist] = useState<ChecklistItem[]>([]);
  const [formatosAviso, setFormatosAviso] = useState('');
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState('');
  const [msg, setMsg] = useState('');
  const [paginasDoc, setPaginasDoc] = useState<{
    id: number;
    nome: string;
    paginaAlvo: number | null;
    trechoAlvo: string;
    pags: { pagina: number; texto: string }[];
  } | null>(null);
  const [novoCheck, setNovoCheck] = useState('');
  const [novaCat, setNovaCat] = useState('');
  const [editDrafts, setEditDrafts] = useState<Record<string, string>>({});
  const [evDrafts, setEvDrafts] = useState<
    Record<string, { documento_id: string; pagina: string; trecho: string }>
  >({});
  const [anexosRemotos, setAnexosRemotos] = useState<AnexoRemoto[] | null>(null);
  const [anexosAviso, setAnexosAviso] = useState('');
  const [anexosBusy, setAnexosBusy] = useState(false);

  const reload = useCallback(async () => {
    setLoading(true);
    setErro('');
    try {
      const data = await fetchAnalise(numero);
      setFicha(data.ficha);
      setDocs(data.documentos);
      setChecklist(data.checklist);
      setFormatosAviso(
        'Formatos: PDF (texto/OCR), DOCX e TXT · máx. 25 MB · anexos PNCP sob demanda · IA local opcional abaixo.',
      );
      const drafts: Record<string, string> = {};
      const evs: Record<string, { documento_id: string; pagina: string; trecho: string }> = {};
      for (const c of data.ficha.campos) {
        drafts[c.chave] = c.valor;
        evs[c.chave] = {
          documento_id: c.documento_id != null ? String(c.documento_id) : '',
          pagina: c.pagina != null ? String(c.pagina) : '',
          trecho: c.trecho || '',
        };
      }
      setEditDrafts(drafts);
      setEvDrafts(evs);
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Erro ao carregar documentos/análise');
    } finally {
      setLoading(false);
    }
  }, [numero]);

  useEffect(() => {
    void reload();
  }, [reload]);

  async function onUpload(file: File | null) {
    if (!file) return;
    setMsg('');
    setErro('');
    try {
      const res = await uploadDocumento(numero, file);
      setMsg(res.aviso || 'Documento guardado.');
      await reload();
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Falha no upload');
    }
  }

  async function onReprocessarOcr(doc: DocumentoMeta) {
    setMsg('');
    setErro('');
    try {
      const res = await reprocessarDocumentoOcr(numero, doc.id);
      setMsg(res.aviso || `Documento #${doc.id} reprocessado (${res.documento.status_extracao}).`);
      await reload();
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Falha ao reprocessar OCR');
    }
  }

  async function onListarAnexosPncp() {
    setErro('');
    setMsg('');
    setAnexosBusy(true);
    try {
      const r = await fetchAnexosRemotos(numero);
      setAnexosRemotos(r.items);
      setAnexosAviso(r.aviso);
    } catch (e) {
      setAnexosRemotos(null);
      setErro(e instanceof Error ? e.message : 'Falha ao listar anexos PNCP');
    } finally {
      setAnexosBusy(false);
    }
  }

  async function onBaixarAnexosPncp(todosBaixaveis: boolean) {
    setErro('');
    setMsg('');
    setAnexosBusy(true);
    try {
      const seqs =
        todosBaixaveis || !anexosRemotos
          ? undefined
          : anexosRemotos
              .filter((a) => a.baixavel && !a.ja_local && a.sequencial_documento != null)
              .map((a) => Number(a.sequencial_documento));
      const r = await baixarAnexosRemotos(numero, {
        sequenciais: seqs,
        max_arquivos: 10,
      });
      setMsg(
        r.aviso +
          (r.erros.length ? ` · ${r.erros.length} erro(s)` : '') +
          (r.pulados.length ? ` · ${r.pulados.length} pulado(s)` : ''),
      );
      await reload();
      await onListarAnexosPncp();
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Falha ao baixar anexos');
    } finally {
      setAnexosBusy(false);
    }
  }

  function docSemPaginaObrigatoria(docId: number | null | undefined): boolean {
    if (!docId) return false;
    const d = docs.find((x) => x.id === docId);
    if (!d) return false;
    const mime = String(d.tipo_mime || '').toLowerCase();
    return (
      mime.startsWith('text/') ||
      mime.includes('wordprocessingml') ||
      (d.nome_original || '').toLowerCase().endsWith('.docx')
    );
  }

  async function verPaginas(
    doc: DocumentoMeta,
    opts?: { pagina?: number | null; trecho?: string },
  ) {
    setErro('');
    try {
      const r = await fetchDocumentoPaginas(numero, doc.id);
      setPaginasDoc({
        id: doc.id,
        nome: doc.nome_original,
        paginaAlvo: opts?.pagina ?? null,
        trechoAlvo: opts?.trecho ?? '',
        pags: r.paginas,
      });
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Falha ao abrir texto');
    }
  }

  async function localizarCampo(c: AnaliseCampo) {
    const docId = c.documento_id ?? Number(evDrafts[c.chave]?.documento_id || 0);
    if (!docId) {
      setErro('Vincule um documento à evidência deste campo primeiro.');
      return;
    }
    const doc = docs.find((d) => d.id === docId);
    if (!doc) {
      setErro('Documento da evidência não está na lista.');
      return;
    }
    await verPaginas(doc, {
      pagina: c.pagina ?? (evDrafts[c.chave]?.pagina ? Number(evDrafts[c.chave].pagina) : null),
      trecho: c.trecho || evDrafts[c.chave]?.trecho || '',
    });
  }

  async function salvarCampo(c: AnaliseCampo) {
    setErro('');
    try {
      const ev = evDrafts[c.chave] || { documento_id: '', pagina: '', trecho: '' };
      const docId = ev.documento_id.trim() ? Number(ev.documento_id) : null;
      const semPag = docSemPaginaObrigatoria(docId);
      const pag = !semPag && ev.pagina.trim() ? Number(ev.pagina) : null;
      await saveAnaliseCampo(numero, c.chave, {
        valor: editDrafts[c.chave] ?? '',
        natureza: 'usuario',
        documento_id: docId,
        pagina: pag,
        trecho: ev.trecho,
        limpar_revisao: true,
      });
      setMsg(`Campo “${c.rotulo}” guardado com rastreio (versão do documento preservada).`);
      await reload();
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Falha ao salvar campo');
    }
  }

  async function addCheck() {
    const t = novoCheck.trim();
    if (!t) return;
    try {
      await createChecklistItem(numero, { titulo: t, categoria: novaCat.trim() || undefined });
      setNovoCheck('');
      setNovaCat('');
      await reload();
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Falha no checklist');
    }
  }

  async function setCheckStatus(item: ChecklistItem, status: ChecklistItem['status']) {
    try {
      await patchChecklistItem(numero, item.id, { status });
      await reload();
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Falha ao atualizar checklist');
    }
  }

  if (loading && !ficha) {
    return <p className="muted">Carregando documentos e ficha…</p>;
  }

  return (
    <div className="docs-analise">
      <p className="drawer__hint docs-analise__banner">
        A ficha combina coleta, o que você preenche e, se o modelo local estiver instalado,
        sugestões de IA neste computador (sem nuvem). Texto de PDF/TXT é extraído por página;
        PDF só-imagem: OCR local (Tesseract). DOCX: texto de parágrafos/tabelas (página opcional).
      </p>

      <IaAnalisePanel numero={numero} docs={docs} onApplied={() => void reload()} />

      <section className="drawer__block">
        <h3>Documentos locais</h3>
        <p className="muted">{formatosAviso}</p>
        <label className="btn btn--ghost docs-analise__upload">
          Adicionar arquivo
          <input
            type="file"
            accept=".pdf,.txt,.docx,application/pdf,text/plain,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            hidden
            onChange={(e) => void onUpload(e.target.files?.[0] ?? null)}
          />
        </label>
        <button
          type="button"
          className="btn btn--ghost"
          disabled={anexosBusy}
          onClick={() => void onListarAnexosPncp()}
        >
          {anexosBusy ? 'Consultando PNCP…' : 'Buscar anexos no PNCP'}
        </button>
        {anexosRemotos && anexosRemotos.some((a) => a.baixavel && !a.ja_local) ? (
          <button
            type="button"
            className="btn btn--primary"
            disabled={anexosBusy}
            onClick={() => void onBaixarAnexosPncp(false)}
          >
            Baixar PDF/DOCX/TXT listados
          </button>
        ) : null}
        {anexosAviso ? <p className="drawer__hint">{anexosAviso}</p> : null}
        {anexosRemotos && (
          <ul className="docs-analise__list">
            {anexosRemotos.length === 0 ? (
              <li>
                <span className="muted">Nenhum anexo remoto retornado pelo PNCP.</span>
              </li>
            ) : (
              anexosRemotos.map((a) => (
                <li key={`${a.sequencial_documento}-${a.titulo}`}>
                  <div>
                    <strong>{a.titulo || a.tipo || 'Anexo'}</strong>
                    <span className="muted">
                      {' '}
                      · seq {a.sequencial_documento ?? '—'}
                      {a.tipo ? ` · ${a.tipo}` : ''}
                      {a.ja_local ? ' · já local' : ''}
                      {!a.baixavel && a.motivo_nao_baixavel
                        ? ` · ${a.motivo_nao_baixavel}`
                        : a.baixavel
                          ? ' · baixável'
                          : ''}
                    </span>
                  </div>
                </li>
              ))
            )}
          </ul>
        )}
        {docs.length === 0 ? (
          <p className="muted">Nenhum documento nesta oportunidade.</p>
        ) : (
          <ul className="docs-analise__list">
            {docs.map((d) => (
              <li key={d.id}>
                <div>
                  <strong>{d.nome_original}</strong>
                  <span className="muted">
                    {' '}
                    · v{d.versao} · {d.tipo_mime} · {d.status_extracao}
                    {d.incluido_em ? ` · ${new Date(d.incluido_em).toLocaleString('pt-BR')}` : ''}
                  </span>
                  {d.aviso_extracao && <p className="acomp__err">{d.aviso_extracao}</p>}
                </div>
                <div className="docs-analise__doc-actions">
                  <a
                    className="btn btn--ghost"
                    href={documentoArquivoUrl(numero, d.id)}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Baixar / abrir
                  </a>
                  <button type="button" className="btn btn--ghost" onClick={() => void verPaginas(d)}>
                    Ver texto
                  </button>
                  {(d.status_extracao === 'ocr_necessario' ||
                    d.status_extracao === 'falhou' ||
                    d.status_extracao === 'sem_texto') && (
                    <button
                      type="button"
                      className="btn btn--ghost"
                      onClick={() => void onReprocessarOcr(d)}
                    >
                      Reprocessar OCR
                    </button>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
        {paginasDoc && (
          <div className="docs-analise__pages">
            <header>
              <strong>
                Texto: {paginasDoc.nome}
                {paginasDoc.paginaAlvo != null
                  ? ` — evidência na página ${paginasDoc.paginaAlvo}`
                  : paginasDoc.trechoAlvo
                    ? ' — localize o trecho abaixo'
                    : ''}
              </strong>
              <button type="button" className="btn btn--ghost" onClick={() => setPaginasDoc(null)}>
                Fechar texto
              </button>
            </header>
            {paginasDoc.paginaAlvo != null &&
            !paginasDoc.pags.some((p) => p.pagina === paginasDoc.paginaAlvo) ? (
              <p className="acomp__err">
                Página {paginasDoc.paginaAlvo} está na evidência, mas não há navegação direta —
                abra o arquivo e vá até essa página.
              </p>
            ) : null}
            {paginasDoc.trechoAlvo ? (
              <p className="drawer__hint">Trecho da evidência: “{paginasDoc.trechoAlvo}”</p>
            ) : null}
            {paginasDoc.pags.length === 0 ? (
              <p className="muted">Sem páginas de texto extraídas.</p>
            ) : (
              paginasDoc.pags.map((p) => {
                const alvo = paginasDoc.paginaAlvo != null && p.pagina === paginasDoc.paginaAlvo;
                const trecho = paginasDoc.trechoAlvo.trim().toLowerCase();
                const temTrecho = Boolean(trecho && p.texto.toLowerCase().includes(trecho));
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
      </section>

      <section className="drawer__block">
        <h3>Ficha de análise</h3>
        <p className="muted">
          Status: {ficha?.status ?? '—'}
          {ficha?.motivo_desatualizacao ? ` — ${ficha.motivo_desatualizacao}` : ''}
        </p>
        {ficha?.status === 'desatualizada' && (
          <button
            type="button"
            className="btn btn--primary"
            onClick={() =>
              void confirmarRevisaoFicha(numero)
                .then(() => reload())
                .catch((e) => setErro(e instanceof Error ? e.message : 'Erro'))
            }
          >
            Confirmei a revisão após nova versão
          </button>
        )}
        {ficha?.campos.map((c) => {
          const draftDocId = Number(evDrafts[c.chave]?.documento_id || 0) || null;
          const semPag = docSemPaginaObrigatoria(draftDocId ?? c.documento_id);
          return (
          <div key={c.chave} className="docs-analise__campo">
            <label>
              {c.rotulo}
              <span className="pill">{NATUREZA_LABEL[c.natureza] ?? c.natureza}</span>
              {c.precisa_revisao && <span className="pill">Revisar</span>}
              {c.revisao_origem === 'usuario' && !c.precisa_revisao ? (
                <span className="pill">Revisado por você</span>
              ) : null}
            </label>
            <textarea
              rows={2}
              value={editDrafts[c.chave] ?? ''}
              onChange={(e) => setEditDrafts((d) => ({ ...d, [c.chave]: e.target.value }))}
              placeholder="Não informado / preencha se souber"
            />
            <div className="docs-analise__check-add">
              <select
                aria-label={`Documento evidência ${c.rotulo}`}
                value={evDrafts[c.chave]?.documento_id ?? ''}
                onChange={(e) =>
                  setEvDrafts((d) => ({
                    ...d,
                    [c.chave]: {
                      ...(d[c.chave] || { pagina: '', trecho: '' }),
                      documento_id: e.target.value,
                      pagina: d[c.chave]?.pagina ?? '',
                      trecho: d[c.chave]?.trecho ?? '',
                    },
                  }))
                }
              >
                <option value="">Sem documento vinculado</option>
                {docs.map((d) => (
                  <option key={d.id} value={d.id}>
                    #{d.id} {d.nome_original} (v{d.versao})
                  </option>
                ))}
              </select>
              {semPag ? (
                <span className="muted">Sem página (TXT/DOCX)</span>
              ) : (
                <input
                  placeholder="Pág. (opcional)"
                  aria-label={`Página evidência ${c.rotulo}`}
                  value={evDrafts[c.chave]?.pagina ?? ''}
                  onChange={(e) =>
                    setEvDrafts((d) => ({
                      ...d,
                      [c.chave]: {
                        documento_id: d[c.chave]?.documento_id ?? '',
                        pagina: e.target.value,
                        trecho: d[c.chave]?.trecho ?? '',
                      },
                    }))
                  }
                />
              )}
            </div>
            <input
              placeholder="Trecho de origem (opcional)"
              value={evDrafts[c.chave]?.trecho ?? ''}
              onChange={(e) =>
                setEvDrafts((d) => ({
                  ...d,
                  [c.chave]: {
                    documento_id: d[c.chave]?.documento_id ?? '',
                    pagina: d[c.chave]?.pagina ?? '',
                    trecho: e.target.value,
                  },
                }))
              }
            />
            {(c.documento_id || c.trecho || c.pagina != null) && (
              <p className="drawer__hint">
                Evidência: doc #{c.documento_id ?? '—'}
                {c.pagina != null
                  ? ` · página ${c.pagina}`
                  : semPag
                    ? ' · sem página (TXT/DOCX)'
                    : ' · página não informada'}
                {c.trecho ? ` · “${c.trecho.slice(0, 80)}”` : ''}
              </p>
            )}
            <div className="docs-analise__doc-actions">
              <button type="button" className="btn btn--ghost" onClick={() => void salvarCampo(c)}>
                Guardar este campo
              </button>
              {(c.documento_id || draftDocId) && (
                <>
                  <a
                    className="btn btn--ghost"
                    href={documentoArquivoUrl(numero, c.documento_id || draftDocId!)}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Abrir documento
                  </a>
                  <button
                    type="button"
                    className="btn btn--ghost"
                    onClick={() => void localizarCampo(c)}
                  >
                    Localizar evidência
                  </button>
                </>
              )}
              <button
                type="button"
                className="btn btn--ghost"
                onClick={() =>
                  void checklistFromCampo(numero, c.chave)
                    .then(() => reload())
                    .catch((e) => setErro(e instanceof Error ? e.message : 'Erro'))
                }
              >
                Criar item de checklist
              </button>
            </div>
          </div>
          );
        })}
      </section>

      <section className="drawer__block">
        <h3>Orientação de participação (checklist)</h3>
        <p className="drawer__hint">
          Organize o que precisa providenciar. Não declara habilitação e não envia nada a
          plataformas.
        </p>
        <div className="docs-analise__check-add">
          <input
            type="text"
            value={novoCheck}
            onChange={(e) => setNovoCheck(e.target.value)}
            placeholder="Ex.: Providenciar certidão federal"
          />
          <input
            type="text"
            value={novaCat}
            onChange={(e) => setNovaCat(e.target.value)}
            placeholder="Categoria (opcional)"
          />
          <button type="button" className="btn btn--primary" onClick={() => void addCheck()}>
            Incluir
          </button>
        </div>
        <ul className="docs-analise__list">
          {checklist.map((item) => (
            <li key={item.id}>
              <div>
                <strong>{item.titulo}</strong>
                {item.categoria ? <p className="muted">Categoria: {item.categoria}</p> : null}
                {item.descricao && <p className="muted">{item.descricao}</p>}
                {item.requisito_chave && (
                  <p className="drawer__hint">Requisito: {item.requisito_chave}</p>
                )}
                <div className="docs-analise__check-add">
                  <input
                    type="text"
                    defaultValue={item.prazo_conhecido || ''}
                    placeholder="Prazo (se conhecido)"
                    aria-label={`Prazo de ${item.titulo}`}
                    onBlur={(e) => {
                      const v = e.target.value.trim();
                      if (v !== (item.prazo_conhecido || '')) {
                        void patchChecklistItem(numero, item.id, { prazo_conhecido: v }).then(
                          () => reload(),
                        );
                      }
                    }}
                  />
                  <input
                    type="text"
                    defaultValue={item.responsavel || ''}
                    placeholder="Responsável (se aplicável)"
                    aria-label={`Responsável de ${item.titulo}`}
                    onBlur={(e) => {
                      const v = e.target.value.trim();
                      if (v !== (item.responsavel || '')) {
                        void patchChecklistItem(numero, item.id, { responsavel: v }).then(
                          () => reload(),
                        );
                      }
                    }}
                  />
                </div>
              </div>
              <select
                value={item.status}
                onChange={(e) =>
                  void setCheckStatus(item, e.target.value as ChecklistItem['status'])
                }
                aria-label={`Status de ${item.titulo}`}
              >
                <option value="pendente">Pendente</option>
                <option value="em_andamento">Em andamento</option>
                <option value="concluido">Concluído</option>
                <option value="nao_aplicavel">Não aplicável</option>
                <option value="bloqueada">Bloqueada</option>
              </select>
              {(item.requisito_chave || item.evidencia_documento_id) && (
                <p className="drawer__hint">
                  Rastreio: requisito {item.requisito_chave || '—'} · doc #
                  {item.evidencia_documento_id ?? '—'} · pág. {item.evidencia_pagina ?? '—'}
                </p>
              )}
            </li>
          ))}
        </ul>
      </section>

      {msg && <p className="acomp__ok">{msg}</p>}
      {erro && <p className="acomp__err">{erro}</p>}
    </div>
  );
}
