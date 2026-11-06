import { useCallback, useEffect, useState } from 'react';
import {
  aplicarSugestaoIa,
  fetchIaAnalise,
  fetchIaJob,
  iniciarIaAnalise,
  rejeitarSugestaoIa,
  type IaJob,
  type IaStatus,
  type IaSugestao,
} from '../api';
import type { DocumentoMeta } from '../types';

type Props = {
  numero: string;
  docs: DocumentoMeta[];
  onApplied?: () => void;
};

function evidenciaLabel(s: IaSugestao): string {
  const doc =
    s.documento_id != null
      ? `doc #${s.documento_id}` +
        (s.documento_versao != null ? ` v${s.documento_versao}` : '') +
        (s.documento_nome ? ` (${s.documento_nome})` : '')
      : 'doc —';
  const pagina =
    s.pagina != null
      ? ` · página ${s.pagina}`
      : s.documento_mime?.includes('pdf')
        ? ' · página ausente'
        : ' · sem página (TXT)';
  const trecho = s.trecho ? ` · “${s.trecho.slice(0, 120)}${s.trecho.length > 120 ? '…' : ''}”` : '';
  return `Evidência: ${doc}${pagina}${trecho}`;
}

function SugestaoItem({
  s,
  busy,
  onAplicar,
  onRejeitar,
}: {
  s: IaSugestao;
  busy: boolean;
  onAplicar: (s: IaSugestao) => void;
  onRejeitar: (s: IaSugestao) => void;
}) {
  const confirmada = Boolean(s.referencia_confirmada);
  return (
    <li>
      <div>
        <strong>
          [{s.tipo}] {s.titulo || s.chave}{' '}
          {confirmada ? (
            <span className="muted">· Confirmada</span>
          ) : (
            <span className="acomp__err">· Não confirmada</span>
          )}
        </strong>
        <p>{s.valor}</p>
        <p className="drawer__hint">{evidenciaLabel(s)}</p>
        <p className={confirmada ? 'muted' : 'acomp__err'}>
          {confirmada
            ? 'Trecho confirmado no texto extraído do documento.'
            : s.aviso_referencia ||
              'Referência não confirmada. Não é possível aplicar pela IA — use o fluxo manual se quiser registrar.'}
        </p>
        {!confirmada ? (
          <p className="drawer__hint">
            Para gravar este valor com origem sua, edite a ficha, requisito ou checklist no fluxo
            manual (não inventamos trecho para completar a sugestão).
          </p>
        ) : null}
        <div className="docs-analise__doc-actions">
          <button
            type="button"
            className="btn btn--primary"
            disabled={busy || !confirmada}
            title={
              confirmada
                ? 'Aplicar após revisão'
                : 'Bloqueado: evidência não confirmada'
            }
            onClick={() => onAplicar(s)}
          >
            Aplicar após revisão
          </button>
          <button
            type="button"
            className="btn btn--ghost"
            disabled={busy}
            onClick={() => onRejeitar(s)}
          >
            Rejeitar
          </button>
        </div>
      </div>
    </li>
  );
}

export function IaAnalisePanel({ numero, docs, onApplied }: Props) {
  const [status, setStatus] = useState<IaStatus | null>(null);
  const [jobs, setJobs] = useState<IaJob[]>([]);
  const [sugestoes, setSugestoes] = useState<IaSugestao[]>([]);
  const [aviso, setAviso] = useState('');
  const [selecionados, setSelecionados] = useState<Record<number, boolean>>({});
  const [jobAtivo, setJobAtivo] = useState<IaJob | null>(null);
  const [erro, setErro] = useState('');
  const [msg, setMsg] = useState('');
  const [busy, setBusy] = useState(false);

  const reload = useCallback(async () => {
    setErro('');
    try {
      const data = await fetchIaAnalise(numero);
      setStatus(data.status);
      setJobs(data.jobs);
      setSugestoes(data.sugestoes_pendentes);
      setAviso(data.aviso);
      const ativo = data.jobs.find((j) => j.status === 'processando' || j.status === 'pendente');
      if (ativo) setJobAtivo(ativo);
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Falha ao carregar IA local');
    }
  }, [numero]);

  useEffect(() => {
    void reload();
  }, [reload]);

  useEffect(() => {
    if (!jobAtivo || (jobAtivo.status !== 'processando' && jobAtivo.status !== 'pendente')) {
      return;
    }
    const t = window.setInterval(() => {
      void fetchIaJob(numero, jobAtivo.id)
        .then((j) => {
          setJobAtivo(j);
          if (j.status !== 'processando' && j.status !== 'pendente') {
            void reload();
            onApplied?.();
          }
        })
        .catch((e) => {
          setErro(
            e instanceof Error
              ? `Falha ao acompanhar análise: ${e.message}`
              : 'Falha ao acompanhar análise local',
          );
        });
    }, 2500);
    return () => window.clearInterval(t);
  }, [jobAtivo, numero, reload, onApplied]);

  function toggleDoc(id: number) {
    setSelecionados((s) => ({ ...s, [id]: !s[id] }));
  }

  async function iniciar() {
    const ids = Object.entries(selecionados)
      .filter(([, v]) => v)
      .map(([k]) => Number(k));
    if (!ids.length) {
      setErro('Selecione ao menos um documento.');
      return;
    }
    setBusy(true);
    setErro('');
    setMsg('');
    try {
      const res = await iniciarIaAnalise(numero, ids);
      setJobAtivo(res.job);
      setStatus(res.status);
      setMsg(
        res.job.status === 'falhou'
          ? res.job.erro || 'IA local indisponível — fluxo manual segue ok.'
          : 'Análise local iniciada. Aguarde o processamento neste computador.',
      );
      await reload();
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Falha ao iniciar análise');
    } finally {
      setBusy(false);
    }
  }

  async function aplicar(s: IaSugestao) {
    if (!s.referencia_confirmada) {
      setErro(
        'Sugestão não confirmada: não dá para aplicar pela IA. Use o fluxo manual se quiser registrar o valor.',
      );
      return;
    }
    setBusy(true);
    setErro('');
    try {
      await aplicarSugestaoIa(numero, s.id);
      setMsg(`Sugestão #${s.id} aplicada (ainda exige sua confirmação na ficha/requisito).`);
      await reload();
      onApplied?.();
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Falha ao aplicar');
    } finally {
      setBusy(false);
    }
  }

  async function rejeitar(s: IaSugestao) {
    setBusy(true);
    try {
      await rejeitarSugestaoIa(numero, s.id);
      await reload();
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Falha ao rejeitar');
    } finally {
      setBusy(false);
    }
  }

  const disponivel = Boolean(status?.disponivel);
  const confirmadas = sugestoes.filter((s) => s.referencia_confirmada);
  const naoConfirmadas = sugestoes.filter((s) => !s.referencia_confirmada);
  const emAnalise =
    jobAtivo != null && (jobAtivo.status === 'processando' || jobAtivo.status === 'pendente');

  return (
    <section className="drawer__block" id="ia-analise-local">
      <h3>Análise local por IA</h3>
      <p className="drawer__hint">
        Somente neste computador (sem nuvem). Sugestões só aplicáveis com evidência confirmada
        (documento, versão e trecho). Campos que você já preencheu (origem usuário) não são
        sobrescritos pela IA — altere pela ficha manual. Limitações: análise pode ser lenta neste
        equipamento; OCR não implementado; PDF só-imagem não entra na IA.
      </p>
      <p className="muted">
        Status: {disponivel ? 'modelo local disponível' : 'IA local indisponível'}
        {status?.modelo_configurado ? ` · modelo ${status.modelo_configurado}` : ''}
        {status?.base_url ? ` · ${status.base_url}` : ''}
        {status?.nuvem ? ' · AVISO: nuvem' : ' · sem nuvem'}
      </p>
      {status?.aviso ? <p className="drawer__hint">{status.aviso}</p> : null}
      {aviso ? <p className="muted">{aviso}</p> : null}

      <div className="docs-analise__list">
        {docs.length === 0 ? (
          <p className="muted">Inclua documentos antes de analisar.</p>
        ) : (
          <ul className="docs-analise__list">
            {docs.map((d) => (
              <li key={d.id}>
                <label className="acomp__label">
                  <input
                    type="checkbox"
                    checked={Boolean(selecionados[d.id])}
                    onChange={() => toggleDoc(d.id)}
                    disabled={busy || emAnalise || d.status_extracao === 'ocr_necessario'}
                  />{' '}
                  #{d.id} {d.nome_original} (v{d.versao}) · {d.status_extracao}
                  {d.status_extracao === 'ocr_necessario'
                    ? ' — OCR não autorizado; não pode ser analisado pela IA'
                    : ''}
                </label>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="docs-analise__doc-actions">
        <button
          type="button"
          className="btn btn--primary"
          disabled={busy || emAnalise || docs.length === 0}
          onClick={() => void iniciar()}
        >
          {emAnalise ? 'Análise em andamento…' : 'Analisar documentos selecionados'}
        </button>
      </div>

      {jobAtivo ? (
        <p className="drawer__hint" aria-live="polite">
          Job #{jobAtivo.id}: <strong>{jobAtivo.status}</strong>
          {jobAtivo.progresso ? ` — ${jobAtivo.progresso}` : ''}
          {jobAtivo.cobertura ? ` · ${jobAtivo.cobertura}` : ''}
          {jobAtivo.erro ? ` · erro: ${jobAtivo.erro}` : ''}
        </p>
      ) : null}

      {jobs[0] && (!jobAtivo || jobAtivo.id !== jobs[0].id) ? (
        <p className="muted">
          Último job #{jobs[0].id}: {jobs[0].status}
          {jobs[0].progresso ? ` — ${jobs[0].progresso}` : ''}
        </p>
      ) : null}

      <h4>Sugestões pendentes de revisão</h4>
      <p className="drawer__hint">
        Aplicar não altera campo com origem usuário. Se a sugestão conflitar, rejeite-a e edite a
        ficha manualmente.
      </p>
      {sugestoes.length === 0 ? (
        <p className="muted">Nenhuma sugestão pendente.</p>
      ) : (
        <>
          {confirmadas.length > 0 ? (
            <>
              <h5>Confirmadas ({confirmadas.length}) — podem ser aplicadas após revisão</h5>
              <ul className="docs-analise__list">
                {confirmadas.map((s) => (
                  <SugestaoItem
                    key={s.id}
                    s={s}
                    busy={busy}
                    onAplicar={(x) => void aplicar(x)}
                    onRejeitar={(x) => void rejeitar(x)}
                  />
                ))}
              </ul>
            </>
          ) : null}
          {naoConfirmadas.length > 0 ? (
            <>
              <h5>
                Não confirmadas ({naoConfirmadas.length}) — não aplicáveis pela IA
              </h5>
              <ul className="docs-analise__list">
                {naoConfirmadas.map((s) => (
                  <SugestaoItem
                    key={s.id}
                    s={s}
                    busy={busy}
                    onAplicar={(x) => void aplicar(x)}
                    onRejeitar={(x) => void rejeitar(x)}
                  />
                ))}
              </ul>
            </>
          ) : null}
        </>
      )}
      {msg && <p className="acomp__ok">{msg}</p>}
      {erro && <p className="acomp__err">{erro}</p>}
    </section>
  );
}
