import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  fetchAcompanhamentoLista,
  fetchAlertas,
  fetchCobertura,
  fetchContagensAcompanhamento,
  fetchDetalhe,
  fetchEventosRecentes,
  fetchFluxoVista,
  fetchKpis,
  fetchOportunidades,
  getLastSeen,
  markSeenNow,
  type ModoLista,
  type OrdenacaoLista,
} from './api';
import { CadastroManualPanel } from './components/CadastroManualPanel';
import { ResultadosPanel } from './components/ResultadosPanel';
import type {
  Acompanhamento,
  AlertasResposta,
  Cobertura,
  Evento,
  EventosRecentes,
  FiltroAcompanhamento,
  Kpis,
  Oportunidade,
} from './types';
import { AcompanhamentoPanel } from './components/AcompanhamentoPanel';
import { AlertsBanner } from './components/AlertsBanner';
import { CoverageBanner } from './components/CoverageBanner';
import { DetailDrawer } from './components/DetailDrawer';
import { ErrorBanner } from './components/ErrorBanner';
import { ConfiguracoesPanel } from './components/ConfiguracoesPanel';
import { ExplorarPanel, type ExplorarModo } from './components/ExplorarPanel';
import { KpiStrip } from './components/KpiStrip';
import { LoadingSkeleton } from './components/LoadingSkeleton';
import { OportunidadesTable } from './components/OportunidadesTable';
import { PriorityCards } from './components/PriorityCards';
import { RecentChanges } from './components/RecentChanges';
import { Sidebar, type NavId } from './components/Sidebar';
import { TopBar } from './components/TopBar';
import {
  computeKpisExtras,
  countPrazoAte,
  filterOportunidades,
  isRegistroTeste,
  pickPriority,
  type FiltroPrazo,
} from './utils';

type Theme = 'dark' | 'light';

type AcompNav = 'salvas' | 'interesse' | 'prosseguir' | 'nao_prosseguir';
type FluxoNav =
  | 'fluxo_salva'
  | 'fluxo_em_analise'
  | 'fluxo_aguardando_informacoes'
  | 'fluxo_em_preparacao'
  | 'fluxo_participacao_registrada'
  | 'fluxo_em_acompanhamento'
  | 'fluxo_encerrada'
  | 'fluxo_arquivada';
const EXPLORAR_MODOS: ExplorarModo[] = ['orgaos', 'categorias', 'regioes', 'indicadores', 'concorrencia'];

function isAcomp(v: NavId): v is AcompNav {
  return v === 'salvas' || v === 'interesse' || v === 'prosseguir' || v === 'nao_prosseguir';
}

function isFluxo(v: NavId): v is FluxoNav {
  return v.startsWith('fluxo_');
}

function isExplorar(v: NavId): v is ExplorarModo {
  return (EXPLORAR_MODOS as string[]).includes(v);
}

const VISTA_META: Record<
  AcompNav,
  { titulo: string; descricao: string; filtro: FiltroAcompanhamento }
> = {
  salvas: {
    titulo: 'Oportunidades salvas',
    descricao: 'Favoritas locais para olhar depois. Salvar não conclui análise nem participa da licitação.',
    filtro: 'salvas',
  },
  interesse: {
    titulo: 'Interesse em analisar',
    descricao: 'Você marcou interesse em analisar. Interesse ≠ inscrição ou envio de proposta.',
    filtro: 'interesse',
  },
  prosseguir: {
    titulo: 'Decisão: prosseguir',
    descricao: 'Organização local da decisão de seguir avaliando. Não envia proposta automaticamente.',
    filtro: 'prosseguir',
  },
  nao_prosseguir: {
    titulo: 'Decisão: não prosseguir',
    descricao: 'Registradas como não prosseguir, com justificativa opcional.',
    filtro: 'nao_prosseguir',
  },
};

const FLUXO_META: Record<FluxoNav, { titulo: string; descricao: string; estado: string }> = {
  fluxo_salva: {
    titulo: 'Salvas (fluxo)',
    descricao: 'Estado do fluxo local: salva (marcar “Salvar para depois” sincroniza aqui).',
    estado: 'salva',
  },
  fluxo_em_analise: {
    titulo: 'Em análise',
    descricao: 'Estado do fluxo local: em análise. Não envia proposta.',
    estado: 'em_analise',
  },
  fluxo_aguardando_informacoes: {
    titulo: 'Aguardando informações',
    descricao: 'Estado do fluxo local: aguardando informações / esclarecimentos.',
    estado: 'aguardando_informacoes',
  },
  fluxo_em_preparacao: {
    titulo: 'Em preparação',
    descricao: 'Estado do fluxo local: em preparação (checklist/planejamento).',
    estado: 'em_preparacao',
  },
  fluxo_participacao_registrada: {
    titulo: 'Participação registrada',
    descricao: 'Registro local de participação. Não envia proposta a plataformas.',
    estado: 'participacao_registrada',
  },
  fluxo_em_acompanhamento: {
    titulo: 'Em acompanhamento',
    descricao: 'Estado do fluxo local: em acompanhamento de participação/resultados.',
    estado: 'em_acompanhamento',
  },
  fluxo_encerrada: {
    titulo: 'Encerradas',
    descricao: 'Estado do fluxo local: encerrada (ciclo concluído neste computador).',
    estado: 'encerrada',
  },
  fluxo_arquivada: {
    titulo: 'Arquivadas',
    descricao: 'Arquivadas saem da lista geral; o histórico permanece neste computador.',
    estado: 'arquivada',
  },
};

function mapContagens(c: Record<string, number>): Partial<Record<NavId, number>> {
  return {
    salvas: c.salvas ?? 0,
    interesse: c.interesse ?? 0,
    prosseguir: c.prosseguir ?? 0,
    nao_prosseguir: c.nao_prosseguir ?? 0,
    fluxo_salva: c.fluxo_salva ?? 0,
    fluxo_em_analise: c.fluxo_em_analise ?? 0,
    fluxo_aguardando_informacoes: c.fluxo_aguardando_informacoes ?? 0,
    fluxo_em_preparacao: c.fluxo_em_preparacao ?? 0,
    fluxo_participacao_registrada: c.fluxo_participacao_registrada ?? 0,
    fluxo_em_acompanhamento: c.fluxo_em_acompanhamento ?? 0,
    fluxo_encerrada: c.fluxo_encerrada ?? 0,
    fluxo_arquivada: c.fluxo_arquivada ?? 0,
  };
}

function loadTheme(): Theme {
  const saved = localStorage.getItem('otto-theme');
  return saved === 'light' ? 'light' : 'dark';
}

function loadModoPadrao(): ModoLista {
  return localStorage.getItem('licitar-modo-padrao') === 'ti' ? 'ti' : 'geral';
}

function loadOrdenacaoPadrao(): OrdenacaoLista {
  return localStorage.getItem('licitar-ordenacao-padrao') === 'prazo' ? 'prazo' : 'publicacao';
}

export function App() {
  const [theme, setTheme] = useState<Theme>(loadTheme);
  const [vista, setVista] = useState<NavId>('radar');
  const [modo, setModo] = useState<ModoLista>(loadModoPadrao);
  const [ordenacao, setOrdenacao] = useState<OrdenacaoLista>(loadOrdenacaoPadrao);
  const [ordenacaoRotulo, setOrdenacaoRotulo] = useState(
    loadOrdenacaoPadrao() === 'prazo' ? 'Prazo de proposta (mais próximo)' : 'Publicação mais recente',
  );
  const [cobertura, setCobertura] = useState<Cobertura | null>(null);
  const [kpis, setKpis] = useState<Kpis | null>(null);
  const [lista, setLista] = useState<Oportunidade[]>([]);
  const [listaTotalBanco, setListaTotalBanco] = useState(0);
  const [acompItems, setAcompItems] = useState<
    { oportunidade: Oportunidade; acompanhamento: Acompanhamento }[]
  >([]);
  const [acompAviso, setAcompAviso] = useState('');
  const [contagens, setContagens] = useState<Partial<Record<NavId, number>>>({});
  const [recentes, setRecentes] = useState<EventosRecentes | null>(null);
  const [alertas, setAlertas] = useState<AlertasResposta | null>(null);
  const [alertasDismissed, setAlertasDismissed] = useState(false);
  const [notifyEnabled, setNotifyEnabled] = useState(
    () => typeof Notification !== 'undefined' && Notification.permission === 'granted',
  );
  const [sel, setSel] = useState<Oportunidade | null>(null);
  const [selAcomp, setSelAcomp] = useState<Acompanhamento | null>(null);
  const [avisoDados, setAvisoDados] = useState('');
  const [eventos, setEventos] = useState<Evento[]>([]);
  const [detalheLoading, setDetalheLoading] = useState(false);
  const [erro, setErro] = useState('');
  const [loading, setLoading] = useState(true);
  const [busca, setBusca] = useState('');
  const [dias, setDias] = useState<FiltroPrazo>('abertas');
  const [somenteAlta, setSomenteAlta] = useState(false);
  const radarAbort = useRef<AbortController | null>(null);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem('otto-theme', theme);
  }, [theme]);

  useEffect(() => {
    setSomenteAlta(modo === 'ti');
    setDias(modo === 'ti' ? 30 : 'abertas');
  }, [modo]);

  const refreshContagens = useCallback(async () => {
    try {
      const c = await fetchContagensAcompanhamento();
      setContagens(mapContagens(c as Record<string, number>));
    } catch {
      /* ignore */
    }
  }, []);

  const reloadRadar = useCallback(async () => {
    radarAbort.current?.abort();
    const ac = new AbortController();
    radarAbort.current = ac;
    setLoading(true);
    setErro('');
    try {
      const desde = getLastSeen() ?? undefined;
      const signal = ac.signal;
      const [cov, k, listaMeta, ev, al] = await Promise.all([
        fetchCobertura(signal),
        fetchKpis(modo, signal),
        fetchOportunidades(modo, ordenacao, signal),
        fetchEventosRecentes(modo, signal),
        modo === 'ti' ? fetchAlertas(desde, signal) : Promise.resolve(null),
      ]);
      if (signal.aborted) return;
      setCobertura(cov);
      setKpis(k);
      setLista(listaMeta.items);
      setListaTotalBanco(listaMeta.total || k.total || listaMeta.items.length);
      setOrdenacaoRotulo(listaMeta.ordenacao_rotulo);
      setRecentes(ev);
      setAlertas(al);
      setAlertasDismissed(false);
      await refreshContagens();

      if (
        modo === 'ti' &&
        al &&
        typeof Notification !== 'undefined' &&
        Notification.permission === 'granted' &&
        al.novas_alta_confianca > 0
      ) {
        new Notification('LICITAR — novas oportunidades TI', {
          body: `${al.novas_alta_confianca} nova(s) alta confiança`,
          tag: 'otto-novas',
        });
      }
    } catch (e) {
      if (ac.signal.aborted || (e instanceof DOMException && e.name === 'AbortError')) return;
      setErro(e instanceof Error ? e.message : 'Erro ao carregar');
    } finally {
      if (!ac.signal.aborted) setLoading(false);
    }
  }, [modo, ordenacao, refreshContagens]);

  // Evita resposta atrasada de um filtro sobrescrever a vista atual.
  const acompGen = useRef(0);

  const reloadAcomp = useCallback(async () => {
    if (!isAcomp(vista)) return;
    const gen = ++acompGen.current;
    const filtro = VISTA_META[vista].filtro;
    setLoading(true);
    setErro('');
    try {
      const data = await fetchAcompanhamentoLista(filtro);
      if (gen !== acompGen.current) return;
      setAcompItems(data.items);
      setAcompAviso(data.aviso);
      setContagens(mapContagens(data.contagens as Record<string, number>));
    } catch (e) {
      if (gen !== acompGen.current) return;
      setErro(e instanceof Error ? e.message : 'Erro ao carregar acompanhamento');
    } finally {
      if (gen === acompGen.current) setLoading(false);
    }
  }, [vista]);

  const reloadFluxo = useCallback(async () => {
    if (!isFluxo(vista)) return;
    const gen = ++acompGen.current;
    setLoading(true);
    setErro('');
    try {
      const data = await fetchFluxoVista(FLUXO_META[vista].estado);
      if (gen !== acompGen.current) return;
      setAcompItems(
        data.items.map((x) => ({
          oportunidade: x.oportunidade,
          acompanhamento: {
            numero_controle_pncp: x.oportunidade.numero_controle_pncp,
            salva: false,
            interesse: false,
            decisao: 'sem_decisao',
            observacoes: '',
            justificativa: '',
          },
        })),
      );
      setAcompAviso(data.aviso);
      setContagens(
        mapContagens({
          ...(data.contagens || {}),
          fluxo_salva: data.contagens?.salva ?? 0,
          fluxo_em_analise: data.contagens?.em_analise ?? 0,
          fluxo_aguardando_informacoes: data.contagens?.aguardando_informacoes ?? 0,
          fluxo_em_preparacao: data.contagens?.em_preparacao ?? 0,
          fluxo_participacao_registrada: data.contagens?.participacao_registrada ?? 0,
          fluxo_em_acompanhamento: data.contagens?.em_acompanhamento ?? 0,
          fluxo_encerrada: data.contagens?.encerrada ?? 0,
          fluxo_arquivada: data.contagens?.arquivada ?? 0,
        }),
      );
    } catch (e) {
      if (gen !== acompGen.current) return;
      setErro(e instanceof Error ? e.message : 'Erro ao carregar fluxo');
    } finally {
      if (gen === acompGen.current) setLoading(false);
    }
  }, [vista]);

  useEffect(() => {
    if (vista === 'radar') {
      void reloadRadar();
      return;
    }
    if (
      isExplorar(vista) ||
      vista === 'configuracoes' ||
      vista === 'cadastro_manual' ||
      vista === 'resultados'
    ) {
      setLoading(false);
      setErro('');
      return;
    }
    setLoading(true);
    setAcompItems([]);
    if (isFluxo(vista)) {
      void reloadFluxo();
      return;
    }
    void reloadAcomp();
  }, [vista, reloadRadar, reloadAcomp, reloadFluxo]);

  const listaOperacional = useMemo(
    () => lista.filter((o) => !isRegistroTeste(o)),
    [lista],
  );

  const filtradas = useMemo(
    () =>
      filterOportunidades(listaOperacional, {
        q: busca,
        dias,
        somenteAlta: modo === 'ti' ? somenteAlta : false,
        ocultarTestes: true,
      }),
    [listaOperacional, busca, dias, somenteAlta, modo],
  );

  const extras = useMemo(() => computeKpisExtras(listaOperacional), [listaOperacional]);
  const vencendo7 = useMemo(() => countPrazoAte(listaOperacional, 7), [listaOperacional]);
  const prioridade = useMemo(
    () => pickPriority(filtradas, 5, { modo, ordenacao }),
    [filtradas, modo, ordenacao],
  );
  // Total do banco (API), descontando manuais de teste já carregados — não o limit da página.
  const kpiTotal = Math.max(
    0,
    (listaTotalBanco || kpis?.total || lista.length) - (lista.length - listaOperacional.length),
  );
  const semDados = !loading && !erro && listaOperacional.length === 0;

  async function abrirDetalhe(o: Oportunidade) {
    setSel(o);
    setDetalheLoading(true);
    setEventos([]);
    setSelAcomp(null);
    try {
      const d = await fetchDetalhe(o.numero_controle_pncp);
      setSel(d.oportunidade);
      setEventos(d.eventos);
      setSelAcomp(d.acompanhamento);
      setAvisoDados(d.aviso_dados ?? '');
    } catch {
      setEventos([]);
    } finally {
      setDetalheLoading(false);
    }
  }

  async function abrirPorNumero(numero: string) {
    const found =
      lista.find((o) => o.numero_controle_pncp === numero) ||
      acompItems.find((x) => x.oportunidade.numero_controle_pncp === numero)?.oportunidade;
    if (found) {
      await abrirDetalhe(found);
      return;
    }
    setSel({
      numero_controle_pncp: numero,
      orgao_razao_social: '',
      uf: '',
      objeto_compra: 'Carregando…',
      situacao: '',
      nicho: '',
      confianca_classificacao: 'nenhuma',
      score_total: 0,
      score_detalhe: { valor: 0, urgencia: 0, nicho: 0, recorrencia: 0, labels: {} },
    });
    setDetalheLoading(true);
    try {
      const d = await fetchDetalhe(numero);
      setSel(d.oportunidade);
      setEventos(d.eventos);
      setSelAcomp(d.acompanhamento);
      setAvisoDados(d.aviso_dados ?? '');
    } catch {
      setSel(null);
    } finally {
      setDetalheLoading(false);
    }
  }

  function dismissAlertas() {
    markSeenNow();
    setAlertasDismissed(true);
  }

  async function enableNotify() {
    if (typeof Notification === 'undefined') return;
    const p = await Notification.requestPermission();
    setNotifyEnabled(p === 'granted');
  }

  function fecharDetalhe() {
    setSel(null);
    setSelAcomp(null);
    setEventos([]);
    setDetalheLoading(false);
  }

  async function onAcompChange(a: Acompanhamento) {
    setSelAcomp(a);
    await refreshContagens();
    if (isAcomp(vista)) await reloadAcomp();
  }

  return (
    <div className="shell">
      <Sidebar active={vista} onNavigate={setVista} contagens={contagens} />

      <div className="shell__main">
        {vista === 'radar' ? (
          <TopBar
            busca={busca}
            onBusca={setBusca}
            dias={dias}
            onDias={setDias}
            modo={modo}
            onModo={setModo}
            ordenacao={ordenacao}
            onOrdenacao={setOrdenacao}
            theme={theme}
            onTheme={() => setTheme((t) => (t === 'dark' ? 'light' : 'dark'))}
            onReload={() => void reloadRadar()}
            loading={loading}
          />
        ) : (
          <header className="topbar">
            <div className="topbar__context">
              <span className="pill">
                {vista === 'configuracoes'
                  ? 'Configurações locais'
                  : vista === 'cadastro_manual'
                    ? 'Cadastro manual'
                    : vista === 'resultados'
                      ? 'Resultados locais'
                    : isExplorar(vista)
                      ? 'Explorar dados locais'
                      : isFluxo(vista)
                        ? 'Fluxo local'
                        : 'Acompanhamento local'}
              </span>
            </div>
            <div className="topbar__actions">
              <button
                type="button"
                className="btn btn--ghost"
                onClick={() => setTheme((t) => (t === 'dark' ? 'light' : 'dark'))}
              >
                {theme === 'dark' ? '☀' : '☾'}
              </button>
              {(isAcomp(vista) || isFluxo(vista)) && (
                <button
                  type="button"
                  className="btn btn--primary"
                  onClick={() => void (isFluxo(vista) ? reloadFluxo() : reloadAcomp())}
                  disabled={loading}
                >
                  {loading ? 'Atualizando…' : 'Atualizar'}
                </button>
              )}
            </div>
          </header>
        )}

        <main className="radar">
          {erro && (
            <ErrorBanner
              message={erro}
              onRetry={() =>
                void (vista === 'radar' ? reloadRadar() : isAcomp(vista) ? reloadAcomp() : undefined)
              }
            />
          )}

          {loading && vista === 'radar' && !kpis && <LoadingSkeleton />}

          {!erro && vista === 'radar' && !loading && (
            <>
              <CoverageBanner cobertura={cobertura} ordenacaoRotulo={ordenacaoRotulo} modo={modo} />

              {modo === 'ti' && !alertasDismissed && alertas && (
                <AlertsBanner
                  alertas={alertas}
                  onDismiss={dismissAlertas}
                  onSelect={(n) => void abrirPorNumero(n)}
                  onEnableNotify={() => void enableNotify()}
                  notifyEnabled={notifyEnabled}
                />
              )}

              <KpiStrip
                total={kpiTotal}
                altaConfianca={extras.altaConfianca}
                scoreMedio={extras.scoreMedio}
                orgaosAtivos={extras.orgaosAtivos}
                vencendo7={vencendo7}
                mudancasRecentes={recentes?.total ?? 0}
                modo={modo}
              />

              <div className="radar__mid">
                <PriorityCards
                  items={prioridade}
                  onSelect={(o) => void abrirDetalhe(o)}
                  selected={sel?.numero_controle_pncp}
                  semDados={semDados}
                  filtroAtivo={somenteAlta || busca.length > 0}
                  modo={modo}
                  ordenacaoRotulo={ordenacaoRotulo}
                />

                <RecentChanges
                  total={recentes?.total ?? 0}
                  items={recentes?.items ?? []}
                  loading={loading}
                  onSelect={(n) => void abrirPorNumero(n)}
                />
              </div>

              <OportunidadesTable
                items={filtradas}
                totalBase={listaOperacional.length}
                modo={modo}
                somenteAlta={somenteAlta}
                onSomenteAlta={setSomenteAlta}
                onSelect={(o) => void abrirDetalhe(o)}
                selected={sel?.numero_controle_pncp}
                loading={loading}
                busca={busca}
                ordenacaoRotulo={ordenacaoRotulo}
              />
            </>
          )}

          {!erro && isExplorar(vista) && (
            <ExplorarPanel modo={vista} onSelectOportunidade={(n) => void abrirPorNumero(n)} />
          )}

          {!erro && vista === 'configuracoes' && <ConfiguracoesPanel />}

          {!erro && vista === 'cadastro_manual' && (
            <CadastroManualPanel
              onCreated={(n) => {
                void refreshContagens();
                void abrirPorNumero(n);
              }}
            />
          )}

          {!erro && vista === 'resultados' && (
            <ResultadosPanel onSelect={(o) => void abrirDetalhe(o)} />
          )}

          {!erro && isAcomp(vista) && (
            <AcompanhamentoPanel
              titulo={VISTA_META[vista].titulo}
              descricao={VISTA_META[vista].descricao}
              aviso={acompAviso}
              items={acompItems}
              loading={loading}
              onSelect={(o) => void abrirDetalhe(o)}
              selected={sel?.numero_controle_pncp}
            />
          )}

          {!erro && isFluxo(vista) && (
            <AcompanhamentoPanel
              titulo={FLUXO_META[vista].titulo}
              descricao={FLUXO_META[vista].descricao}
              aviso={acompAviso}
              items={acompItems}
              loading={loading}
              onSelect={(o) => void abrirDetalhe(o)}
              selected={sel?.numero_controle_pncp}
            />
          )}
        </main>
      </div>

      {sel && (
        <DetailDrawer
          oportunidade={sel}
          eventos={eventos}
          acompanhamento={selAcomp}
          avisoDados={avisoDados}
          loading={detalheLoading}
          onClose={fecharDetalhe}
          onAcompanhamentoChange={(a) => void onAcompChange(a)}
          onOportunidadeChange={(o) => {
            setSel(o);
            setLista((prev) =>
              prev.map((x) => (x.numero_controle_pncp === o.numero_controle_pncp ? { ...x, ...o } : x)),
            );
          }}
        />
      )}
    </div>
  );
}
