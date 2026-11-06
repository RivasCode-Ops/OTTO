import { useEffect, useState } from 'react';
import {
  createBackup,
  fetchAprendizado,
  fetchAuditoria,
  fetchConfiguracoes,
  fetchIngestStatus,
  listBackups,
  restoreBackupCopy,
  startIngest,
  type AprendizadoResumo,
  type IngestStatus,
} from '../api';

const PERFIL_KEY = 'licitar-perfil-opcional';
const MODO_KEY = 'licitar-modo-padrao';
const ORD_KEY = 'licitar-ordenacao-padrao';

type PerfilLocal = { nome_empresa: string; cnpj: string; contato: string };

function loadPerfil(): PerfilLocal {
  try {
    const raw = localStorage.getItem(PERFIL_KEY);
    if (!raw) return { nome_empresa: '', cnpj: '', contato: '' };
    const p = JSON.parse(raw) as Partial<PerfilLocal>;
    return {
      nome_empresa: p.nome_empresa ?? '',
      cnpj: p.cnpj ?? '',
      contato: p.contato ?? '',
    };
  } catch {
    return { nome_empresa: '', cnpj: '', contato: '' };
  }
}

export function ConfiguracoesPanel() {
  const [cfg, setCfg] = useState<Awaited<ReturnType<typeof fetchConfiguracoes>> | null>(null);
  const [backups, setBackups] = useState<{ nome: string; bytes: number }[]>([]);
  const [msg, setMsg] = useState('');
  const [erro, setErro] = useState('');
  const [perfil, setPerfil] = useState<PerfilLocal>(loadPerfil);
  const [modoPadrao, setModoPadrao] = useState(
    () => localStorage.getItem(MODO_KEY) || 'geral',
  );
  const [ordPadrao, setOrdPadrao] = useState(
    () => localStorage.getItem(ORD_KEY) || 'publicacao',
  );
  const [auditoria, setAuditoria] = useState<
    { id: number; acao: string; numero_controle_pncp: string | null; detalhe: string; criado_em: string }[]
  >([]);
  const [avisoAud, setAvisoAud] = useState('');
  const [aprendizado, setAprendizado] = useState<AprendizadoResumo | null>(null);
  const [ingest, setIngest] = useState<IngestStatus | null>(null);
  const [ingestDays, setIngestDays] = useState(7);
  const [ingestBusy, setIngestBusy] = useState(false);

  useEffect(() => {
    void (async () => {
      try {
        setCfg(await fetchConfiguracoes());
        const b = await listBackups();
        setBackups(b.items);
        const a = await fetchAuditoria();
        setAuditoria(a.items);
        setAvisoAud(a.aviso);
        setAprendizado(await fetchAprendizado());
        const ing = await fetchIngestStatus();
        setIngest(ing);
        setIngestDays(ing.config.janela_dias_padrao || 7);
      } catch (e) {
        setErro(e instanceof Error ? e.message : 'Falha ao carregar configurações');
      }
    })();
  }, []);

  useEffect(() => {
    if (!ingest?.em_andamento) return;
    const t = window.setInterval(() => {
      void (async () => {
        try {
          const ing = await fetchIngestStatus();
          setIngest(ing);
          if (!ing.em_andamento) {
            const u = ing.ultima_execucao;
            if (u?.mensagem === 'ok') {
              setMsg(
                `Coleta #${u.id} ok: ${u.total_novos ?? 0} novos, ${u.total_atualizados ?? 0} atualizados` +
                  (u.erros ? `, ${u.erros} erros` : ''),
              );
            } else if (u?.mensagem) {
              setErro(`Coleta #${u.id}: ${u.mensagem}`);
            }
          }
        } catch {
          /* poll silencioso; erro aparece no próximo disparo */
        }
      })();
    }, 2500);
    return () => window.clearInterval(t);
  }, [ingest?.em_andamento]);

  async function doIngest() {
    setErro('');
    setMsg('');
    setIngestBusy(true);
    try {
      const r = await startIngest({ days: ingestDays });
      setMsg(`Coleta #${r.id} iniciada (janela ${r.days ?? ingestDays} dias). Aguarde…`);
      setIngest(await fetchIngestStatus());
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Falha ao iniciar coleta');
    } finally {
      setIngestBusy(false);
    }
  }

  async function doBackup() {
    try {
      const r = await createBackup();
      setMsg(`Backup criado: ${r.nome}`);
      const b = await listBackups();
      setBackups(b.items);
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Falha no backup');
    }
  }

  async function doRestore(nome: string) {
    try {
      const r = await restoreBackupCopy(nome);
      setMsg(r.aviso || 'Restaurado em cópia isolada.');
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Falha na restauração isolada');
    }
  }

  if (!cfg && !erro) return <p className="muted">Carregando configurações…</p>;

  return (
    <section className="table-section">
      <header className="section-head">
        <div>
          <h2>Configurações</h2>
          <p className="muted">{cfg?.aviso}</p>
        </div>
      </header>

      {cfg && (
        <>
          <h3>Armazenamento local</h3>
          <ul className="muted">
            <li>Pasta de dados: {cfg.data_dir}</li>
            <li>Banco: {cfg.db_path}</li>
            <li>Documentos: {cfg.documentos_dir}</li>
            <li>Backups: {cfg.backups_dir}</li>
          </ul>

          <h3>Capacidades (estado atual)</h3>
          <ul className="muted">
            <li>Perfil obrigatório: {cfg.perfil_obrigatorio ? 'sim' : 'não'}</li>
            <li>IA na análise: {cfg.ia_analise ? 'ligada' : 'desligada (decisão pendente)'}</li>
            <li>
              OCR:{' '}
              {cfg.ocr
                ? cfg.ocr_disponivel
                  ? 'autorizado e motor local disponível'
                  : 'autorizado — motor Tesseract ausente (docs/OCR.md)'
                : 'desligado'}
            </li>
            {cfg.ocr_status?.aviso ? (
              <li className="muted">{cfg.ocr_status.aviso}</li>
            ) : null}
            <li>DOCX: {cfg.docx ? 'ligado (texto local)' : 'desligado'}</li>
            <li>
              Download de anexos PNCP:{' '}
              {cfg.download_automatico_anexos
                ? 'ligado (só pncp.gov.br · PDF/DOCX/TXT)'
                : 'desligado'}
            </li>
          </ul>

          <h3>Cópia de segurança</h3>
          <p className="drawer__hint">{cfg.restore_operacional.procedimento}</p>
          <p className="drawer__hint">
            O backup zip inclui o banco SQLite e a pasta de documentos. Não inclui o perfil
            opcional nem preferências guardadas neste navegador (localStorage). Não declare o
            backup como “cópia completa de tudo o que o usuário configurou na interface”.
          </p>
          <button type="button" className="btn btn--primary" onClick={() => void doBackup()}>
            Criar backup agora
          </button>
          <ul className="docs-analise__list">
            {backups.map((b) => (
              <li key={b.nome}>
                <span>
                  {b.nome} · {(b.bytes / 1024).toFixed(0)} KB
                </span>
                <button type="button" className="btn btn--ghost" onClick={() => void doRestore(b.nome)}>
                  Restaurar em cópia isolada
                </button>
              </li>
            ))}
          </ul>

          <h3>Coleta PNCP</h3>
          <p className="drawer__hint">
            {ingest?.aviso ||
              'Dispara a mesma coleta do comando otto ingest. Pode demorar; só uma por vez.'}
          </p>
          {ingest && (
            <p className="muted">
              Config: UF {ingest.config.ufs.join(', ') || '—'} · modalidades{' '}
              {ingest.config.modalidades.join(', ') || '—'} · padrão{' '}
              {ingest.config.janela_dias_padrao} dias
              {ingest.em_andamento
                ? ` · em andamento (#${ingest.run_atual?.id ?? '?'}) desde ${ingest.run_atual?.iniciado_em ?? '—'}`
                : ingest.ultima_execucao
                  ? ` · última #${ingest.ultima_execucao.id}: ${ingest.ultima_execucao.mensagem || '—'} (${ingest.ultima_execucao.total_novos ?? 0} novos / ${ingest.ultima_execucao.total_atualizados ?? 0} atualizados)`
                  : ' · ainda sem execução registrada'}
            </p>
          )}
          <label className="acomp__label">
            Janela (dias)
            <select
              value={ingestDays}
              onChange={(e) => setIngestDays(Number(e.target.value))}
              disabled={ingestBusy || !!ingest?.em_andamento}
            >
              <option value={2}>2 (incremental)</option>
              <option value={7}>7 (padrão)</option>
              <option value={14}>14 (semanal)</option>
            </select>
          </label>
          <button
            type="button"
            className="btn btn--primary"
            disabled={ingestBusy || !!ingest?.em_andamento}
            onClick={() => void doIngest()}
          >
            {ingest?.em_andamento ? 'Coleta em andamento…' : 'Atualizar coleta agora'}
          </button>

          {cfg.cobertura && (
            <>
              <h3>Fonte / cobertura</h3>
              <p className="muted">
                Fonte PNCP · ver banner de cobertura na lista geral para UF, última coleta e
                limitações.
              </p>
            </>
          )}

          <h3>Preferências da lista</h3>
          <p className="drawer__hint">
            Guardadas neste navegador. Aplicam-se na próxima abertura da lista geral.
          </p>
          <label className="acomp__label">
            Modo padrão
            <select value={modoPadrao} onChange={(e) => setModoPadrao(e.target.value)}>
              <option value="geral">Todos os setores</option>
              <option value="ti">Radar TI</option>
            </select>
          </label>
          <label className="acomp__label">
            Ordenação padrão
            <select value={ordPadrao} onChange={(e) => setOrdPadrao(e.target.value)}>
              <option value="publicacao">Publicação mais recente</option>
              <option value="prazo">Prazo de proposta</option>
            </select>
          </label>
          <button
            type="button"
            className="btn btn--ghost"
            onClick={() => {
              localStorage.setItem(MODO_KEY, modoPadrao);
              localStorage.setItem(ORD_KEY, ordPadrao);
              setMsg('Preferências da lista guardadas neste navegador.');
            }}
          >
            Guardar preferências da lista
          </button>

          <h3>Perfil opcional</h3>
          <p className="drawer__hint">
            Dados só neste navegador. Opcional: não filtra a lista geral nem oculta setores. Não é
            login nem multiusuário.
          </p>
          <label className="acomp__label">
            Nome da empresa
            <input
              value={perfil.nome_empresa}
              onChange={(e) => setPerfil({ ...perfil, nome_empresa: e.target.value })}
            />
          </label>
          <label className="acomp__label">
            CNPJ (opcional)
            <input
              value={perfil.cnpj}
              onChange={(e) => setPerfil({ ...perfil, cnpj: e.target.value })}
            />
          </label>
          <label className="acomp__label">
            Contato (opcional)
            <input
              value={perfil.contato}
              onChange={(e) => setPerfil({ ...perfil, contato: e.target.value })}
            />
          </label>
          <button
            type="button"
            className="btn btn--primary"
            onClick={() => {
              localStorage.setItem(PERFIL_KEY, JSON.stringify(perfil));
              setMsg('Perfil opcional guardado neste navegador. A lista geral não é filtrada por ele.');
            }}
          >
            Guardar perfil opcional
          </button>

          <h3>Aprendizado do histórico (local)</h3>
          {aprendizado ? (
            <>
              <p className="drawer__hint">{aprendizado.aviso}</p>
              {aprendizado.influencia_analise ? (
                <p className="muted">
                  Influência no prompt da próxima análise:{' '}
                  {aprendizado.influencia_analise.ativa ? (
                    <strong>ativa</strong>
                  ) : (
                    <strong>inativa</strong>
                  )}{' '}
                  ({aprendizado.influencia_analise.decisoes}/
                  {aprendizado.influencia_analise.minimo} decisões mín.)
                  {aprendizado.influencia_analise.chaves_preferidas.length
                    ? ` · preferir: ${aprendizado.influencia_analise.chaves_preferidas.join(', ')}`
                    : ''}
                  {aprendizado.influencia_analise.chaves_evitar.length
                    ? ` · evitar sem evidência forte: ${aprendizado.influencia_analise.chaves_evitar.join(', ')}`
                    : ''}
                </p>
              ) : null}
              <ul className="docs-analise__list">
                {aprendizado.insights.map((ins) => (
                  <li key={ins}>
                    <span>{ins}</span>
                  </li>
                ))}
              </ul>
              <p className="muted">
                Auditoria: {aprendizado.acoes.total} · IA aplicadas:{' '}
                {aprendizado.ia_sugestoes.aplicadas} · rejeitadas:{' '}
                {aprendizado.ia_sugestoes.rejeitadas} · pendentes:{' '}
                {aprendizado.ia_sugestoes.pendentes}
                {aprendizado.ia_sugestoes.taxa_aceitacao != null
                  ? ` · aceitação ≈ ${Math.round(aprendizado.ia_sugestoes.taxa_aceitacao * 100)}%`
                  : ''}
                {' · '}
                oportunidades com resultado: {aprendizado.resultados.com_resultado}
              </p>
              {aprendizado.ia_sugestoes.amostras_aplicadas.length > 0 ? (
                <>
                  <h4>Últimas sugestões aplicadas</h4>
                  <ul className="docs-analise__list">
                    {aprendizado.ia_sugestoes.amostras_aplicadas.map((s) => (
                      <li key={`ap-${s.id}`}>
                        <span>
                          [{s.tipo}] {s.titulo || s.chave} — {s.valor}
                          {s.numero_controle_pncp ? ` · ${s.numero_controle_pncp}` : ''}
                        </span>
                      </li>
                    ))}
                  </ul>
                </>
              ) : null}
              {aprendizado.ia_sugestoes.amostras_rejeitadas.length > 0 ? (
                <>
                  <h4>Últimas sugestões rejeitadas</h4>
                  <ul className="docs-analise__list">
                    {aprendizado.ia_sugestoes.amostras_rejeitadas.map((s) => (
                      <li key={`rj-${s.id}`}>
                        <span>
                          [{s.tipo}] {s.titulo || s.chave} — {s.valor}
                          {s.numero_controle_pncp ? ` · ${s.numero_controle_pncp}` : ''}
                        </span>
                      </li>
                    ))}
                  </ul>
                </>
              ) : null}
            </>
          ) : (
            <p className="muted">Carregando resumo do histórico…</p>
          )}

          <h3>Auditoria local</h3>
          <p className="drawer__hint">{avisoAud}</p>
          {auditoria.length === 0 ? (
            <p className="muted">Nenhuma ação registrada ainda.</p>
          ) : (
            <ul className="docs-analise__list">
              {auditoria.slice(0, 30).map((a) => (
                <li key={a.id}>
                  <span>
                    {a.criado_em} · {a.acao}
                    {a.numero_controle_pncp ? ` · ${a.numero_controle_pncp}` : ''}
                    {a.detalhe ? ` — ${a.detalhe}` : ''}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </>
      )}

      {msg && <p className="acomp__ok">{msg}</p>}
      {erro && <p className="acomp__err">{erro}</p>}
    </section>
  );
}
