import { useEffect, useState } from 'react';
import { fmtDate, fmtMoney, patchPrazosManuais, saveAcompanhamento, saveFluxo } from '../api';
import type { Acompanhamento, DecisaoUsuario, Evento, Oportunidade } from '../types';
import { ClassificacaoPanel } from './ClassificacaoPanel';
import { ContinuidadePanel } from './ContinuidadePanel';
import { DocsAnalisePanel } from './DocsAnalisePanel';
import { ItensLotesPanel } from './ItensLotesPanel';
import { OrientacaoPanel } from './OrientacaoPanel';
import { RequisitosPanel } from './RequisitosPanel';
import { getMunicipio } from '../utils';

type Props = {
  oportunidade: Oportunidade;
  eventos: Evento[];
  acompanhamento: Acompanhamento | null;
  avisoDados?: string;
  loading?: boolean;
  onClose: () => void;
  onAcompanhamentoChange: (a: Acompanhamento) => void;
  onOportunidadeChange?: (o: Oportunidade) => void;
};

function Field({ label, value, hint }: { label: string; value: string; hint?: string }) {
  const ausente = !value || value === '—' || value === 'Não informado';
  return (
    <div className={`drawer-field ${ausente ? 'drawer-field--empty' : ''}`}>
      <span className="drawer__label">{label}</span>
      {hint && <span className="drawer__hint-inline">{hint}</span>}
      <p>{ausente ? 'Não informado' : value}</p>
    </div>
  );
}

function textOrEmpty(v?: string | null): string {
  const t = (v ?? '').trim();
  return t || 'Não informado';
}

export function DetailDrawer({
  oportunidade: o,
  eventos,
  acompanhamento,
  avisoDados,
  loading,
  onClose,
  onAcompanhamentoChange,
  onOportunidadeChange,
}: Props) {
  const [ac, setAc] = useState<Acompanhamento | null>(acompanhamento);
  const [obs, setObs] = useState(acompanhamento?.observacoes ?? '');
  const [just, setJust] = useState(acompanhamento?.justificativa ?? '');
  const [esc, setEsc] = useState(o.data_esclarecimento?.slice(0, 10) ?? '');
  const [imp, setImp] = useState(o.data_impugnacao?.slice(0, 10) ?? '');
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState('');
  const [erro, setErro] = useState('');

  useEffect(() => {
    setAc(acompanhamento);
    setObs(acompanhamento?.observacoes ?? '');
    setJust(acompanhamento?.justificativa ?? '');
    setEsc(o.data_esclarecimento?.slice(0, 10) ?? '');
    setImp(o.data_impugnacao?.slice(0, 10) ?? '');
    setMsg('');
    setErro('');
  }, [acompanhamento, o.numero_controle_pncp, o.data_esclarecimento, o.data_impugnacao]);

  async function patch(partial: Parameters<typeof saveAcompanhamento>[1]) {
    setSaving(true);
    setErro('');
    try {
      const res = await saveAcompanhamento(o.numero_controle_pncp, partial);
      setAc(res.acompanhamento);
      setObs(res.acompanhamento.observacoes);
      setJust(res.acompanhamento.justificativa);
      onAcompanhamentoChange(res.acompanhamento);
      setMsg(res.aviso);
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Erro ao salvar');
    } finally {
      setSaving(false);
    }
  }

  const municipio = getMunicipio(o);
  const localizacao =
    municipio !== '—' || o.uf
      ? `${municipio !== '—' ? municipio : 'Município não informado'} · ${o.uf || 'UF não informada'}`
      : 'Não informado';

  return (
    <>
      <button type="button" className="drawer-backdrop" aria-label="Fechar detalhe" onClick={onClose} />
      <aside className="drawer drawer--open" role="dialog" aria-labelledby="drawer-title">
        {loading ? (
          <div className="drawer__loading">
            <div className="skeleton-line skeleton-line--title" />
            <div className="skeleton-block skeleton-block--tall" />
            <p className="muted">Carregando detalhe…</p>
          </div>
        ) : (
          <>
            <header className="drawer__head">
              <div>
                <span className="pill">{o.nicho || 'sem nicho'}</span>
                <span className="pill">{o.situacao || 'situação não informada'}</span>
                <span className="pill">
                  {o.origem_registro === 'manual' ? 'Origem: cadastro manual' : 'Origem: PNCP (coleta)'}
                </span>
              </div>
              <button type="button" className="drawer__close" onClick={onClose} aria-label="Fechar">
                ×
              </button>
            </header>

            <h2 id="drawer-title" className="drawer__title">
              Oportunidade
            </h2>
            <p className="drawer__disclaimer">
              {avisoDados ||
                'Dados da coleta PNCP. Não são análise completa do edital nem leitura por IA.'}
            </p>

            <section className="drawer__block">
              <h3>Objeto</h3>
              <p>{textOrEmpty(o.objeto_compra)}</p>
            </section>

            <section className="drawer__block drawer__grid">
              <Field label="Órgão" value={textOrEmpty(o.orgao_razao_social)} />
              <Field label="Localização" value={localizacao} />
              <Field
                label="Identificação"
                value={textOrEmpty(o.numero_controle_pncp)}
                hint="Número de controle PNCP"
              />
              <Field label="Fonte" value="PNCP (coleta local)" />
              <Field label="Modalidade" value={textOrEmpty(o.modalidade)} />
              <Field label="Situação na fonte" value={textOrEmpty(o.situacao)} />
              <Field
                label="Valor estimado"
                value={o.valor_total_estimado != null ? fmtMoney(o.valor_total_estimado) : 'Não informado'}
                hint="Natureza: valor total estimado (quando informado pela fonte)"
              />
              <Field
                label="Valor homologado"
                value={o.valor_total_homologado != null ? fmtMoney(o.valor_total_homologado) : 'Não informado'}
                hint="Natureza: valor total homologado (quando informado)"
              />
              <Field
                label="Data de publicação"
                value={o.data_publicacao ? fmtDate(o.data_publicacao) : 'Não informado'}
                hint="Publicação / inclusão no PNCP"
              />
              <Field
                label="Abertura de propostas"
                value={o.data_abertura ? fmtDate(o.data_abertura) : 'Não informado'}
                hint="Início do prazo de proposta, quando houver"
              />
              <Field
                label="Encerramento de propostas"
                value={o.data_encerramento ? fmtDate(o.data_encerramento) : 'Não informado'}
                hint="Prazo final de proposta, quando houver"
              />
              <Field
                label="Esclarecimento"
                value={o.data_esclarecimento ? fmtDate(o.data_esclarecimento) : 'Não informado'}
                hint="Prazo manual (não vem automaticamente da fonte nesta versão)"
              />
              <Field
                label="Impugnação"
                value={o.data_impugnacao ? fmtDate(o.data_impugnacao) : 'Não informado'}
                hint="Prazo manual (não vem automaticamente da fonte nesta versão)"
              />
              <Field label="Qualidade dos dados" value={textOrEmpty(o.qualidade_dados)} />
            </section>

            <section className="drawer__block">
              <h3>Prazos manuais (esclarecimento / impugnação)</h3>
              <p className="drawer__hint">
                Preencha aqui quando souber. Extração automática desses campos depende de decisão
                de IA/OCR — não é feita nesta versão.
              </p>
              <label className="acomp__label">
                Data esclarecimento
                <input type="date" value={esc} onChange={(e) => setEsc(e.target.value)} />
              </label>
              <label className="acomp__label">
                Data impugnação
                <input type="date" value={imp} onChange={(e) => setImp(e.target.value)} />
              </label>
              <button
                type="button"
                className="btn btn--ghost"
                disabled={saving}
                onClick={() => {
                  void (async () => {
                    setSaving(true);
                    setErro('');
                    try {
                      const r = await patchPrazosManuais(o.numero_controle_pncp, {
                        data_esclarecimento: esc || null,
                        data_impugnacao: imp || null,
                        limpar_esclarecimento: !esc,
                        limpar_impugnacao: !imp,
                      });
                      onOportunidadeChange?.(r.item);
                      setMsg(r.aviso);
                    } catch (e) {
                      setErro(e instanceof Error ? e.message : 'Falha nos prazos');
                    } finally {
                      setSaving(false);
                    }
                  })();
                }}
              >
                Guardar prazos manuais
              </button>
            </section>

            <section className="drawer__block">
              <h3>Link da fonte</h3>
              {o.link_sistema_origem ? (
                <a className="btn btn--primary btn--block" href={o.link_sistema_origem} target="_blank" rel="noreferrer">
                  Abrir link original da fonte
                </a>
              ) : (
                <p className="muted">Link original: Não informado</p>
              )}
              <p className="drawer__hint">
                O link abre o PNCP no navegador. Para gravar anexos aqui: Documentos →
                Buscar anexos no PNCP (PDF/DOCX/TXT).
              </p>
            </section>

            <section className="drawer__block acomp">
              <h3>Seu acompanhamento (local)</h3>
              <p className="drawer__hint">
                Salvar ≠ análise concluída. Interesse ≠ participação. Prosseguir ≠ envio de proposta.
                Nada é enviado a plataformas de licitação.
              </p>
              <div className="acomp__actions">
                <button
                  type="button"
                  className={`btn ${ac?.salva ? 'btn--primary' : 'btn--ghost'}`}
                  disabled={saving}
                  onClick={() => void patch({ salva: !ac?.salva })}
                >
                  {ac?.salva ? 'Salva — cliques para desfazer' : 'Salvar para depois'}
                </button>
                <button
                  type="button"
                  className={`btn ${ac?.interesse ? 'btn--primary' : 'btn--ghost'}`}
                  disabled={saving}
                  onClick={() => void patch({ interesse: !ac?.interesse })}
                >
                  {ac?.interesse ? 'Interesse marcado — desfazer' : 'Tenho interesse em analisar'}
                </button>
                <button
                  type="button"
                  className="btn btn--ghost"
                  onClick={() => {
                    document.getElementById('docs-analise-panel')?.scrollIntoView({ behavior: 'smooth' });
                  }}
                >
                  Analisar documentos
                </button>
                <button
                  type="button"
                  className="btn btn--ghost"
                  disabled={saving}
                  onClick={() =>
                    void patch({
                      decisao: 'nao_prosseguir',
                      justificativa: just || 'Sem interesse nesta oportunidade',
                    })
                  }
                >
                  Não tenho interesse
                </button>
                <button
                  type="button"
                  className="btn btn--ghost"
                  disabled={saving}
                  onClick={() => {
                    void (async () => {
                      setSaving(true);
                      setErro('');
                      try {
                        await saveFluxo(o.numero_controle_pncp, { estado_fluxo: 'arquivada' });
                        setMsg('Arquivada no fluxo local (histórico preservado).');
                      } catch (e) {
                        setErro(e instanceof Error ? e.message : 'Falha ao arquivar');
                      } finally {
                        setSaving(false);
                      }
                    })();
                  }}
                >
                  Arquivar
                </button>
              </div>
              <label className="acomp__label">
                Decisão
                <select
                  value={ac?.decisao ?? 'sem_decisao'}
                  disabled={saving}
                  onChange={(e) => void patch({ decisao: e.target.value as DecisaoUsuario })}
                >
                  <option value="sem_decisao">Sem decisão</option>
                  <option value="prosseguir">Prosseguir (organização local)</option>
                  <option value="nao_prosseguir">Não prosseguir</option>
                </select>
              </label>
              <label className="acomp__label">
                Observações
                <textarea
                  value={obs}
                  rows={3}
                  onChange={(e) => setObs(e.target.value)}
                  placeholder="Anotações livres (opcional)"
                />
              </label>
              <label className="acomp__label">
                Justificativa da decisão
                <textarea
                  value={just}
                  rows={2}
                  onChange={(e) => setJust(e.target.value)}
                  placeholder="Por que prosseguir ou não (opcional)"
                />
              </label>
              <button
                type="button"
                className="btn btn--primary"
                disabled={saving}
                onClick={() => void patch({ observacoes: obs, justificativa: just })}
              >
                {saving ? 'Salvando…' : 'Guardar textos'}
              </button>
              {msg && <p className="acomp__ok">{msg}</p>}
              {erro && <p className="acomp__err">{erro}</p>}
            </section>

            <ClassificacaoPanel numero={o.numero_controle_pncp} />
            <OrientacaoPanel numero={o.numero_controle_pncp} />
            <RequisitosPanel numero={o.numero_controle_pncp} />
            <ItensLotesPanel numero={o.numero_controle_pncp} />
            <div id="docs-analise-panel">
              <DocsAnalisePanel numero={o.numero_controle_pncp} />
            </div>
            <ContinuidadePanel numero={o.numero_controle_pncp} />

            {eventos.length > 0 && (
              <section className="drawer__block">
                <h3>Histórico de mudanças na coleta</h3>
                <ul className="drawer__events">
                  {eventos.map((e) => (
                    <li key={e.id}>
                      <span>{e.campo}</span>
                      {e.valor_anterior ?? '—'} → {e.valor_novo ?? '—'}
                      <time>{fmtDate(e.detectado_em)}</time>
                    </li>
                  ))}
                </ul>
              </section>
            )}

            <footer className="drawer__foot">
              <p className="drawer__id muted">{o.numero_controle_pncp}</p>
            </footer>
          </>
        )}
      </aside>
    </>
  );
}
