import { useState } from 'react';
import type { EscopoUf, ModoLista, OrdenacaoLista } from '../api';
import type { FiltroPrazo } from '../utils';

export type NichoFiltro = 'todos' | string;

type Props = {
  busca: string;
  onBusca: (v: string) => void;
  dias: FiltroPrazo;
  onDias: (v: FiltroPrazo) => void;
  modo: ModoLista;
  onModo: (v: ModoLista) => void;
  ordenacao: OrdenacaoLista;
  onOrdenacao: (v: OrdenacaoLista) => void;
  mostrarTestes: boolean;
  onMostrarTestes: (v: boolean) => void;
  escopoUf: EscopoUf;
  onEscopoUf: (v: EscopoUf) => void;
  ufsConfig: string[];
  ufsPresentes: string[];
  nicho: NichoFiltro;
  onNicho: (v: NichoFiltro) => void;
  nichoOpcoes: { id: string; label: string; count: number }[];
  theme: 'dark' | 'light';
  onTheme: () => void;
  onReload: () => void;
  loading: boolean;
};

function parsePrazo(v: string): FiltroPrazo {
  if (v === 'abertas') return 'abertas';
  return Number(v);
}

function rotuloColeta(ufsConfig: string[]): string {
  const ufs = ufsConfig.length ? ufsConfig.join(', ') : 'coleta';
  return `${ufs} (coleta)`;
}

export function TopBar({
  busca,
  onBusca,
  dias,
  onDias,
  modo,
  onModo,
  ordenacao,
  onOrdenacao,
  mostrarTestes,
  onMostrarTestes,
  escopoUf,
  onEscopoUf,
  ufsConfig,
  ufsPresentes,
  nicho,
  onNicho,
  nichoOpcoes,
  theme,
  onTheme,
  onReload,
  loading,
}: Props) {
  const [menuOpen, setMenuOpen] = useState(false);
  const prazoValue = dias === 'abertas' ? 'abertas' : String(dias);
  const ufsSelect = Array.from(
    new Set([...ufsConfig.map((u) => u.toUpperCase()), ...ufsPresentes.map((u) => u.toUpperCase())]),
  ).filter(Boolean).sort();

  return (
    <header className="topbar">
      <div className="topbar__context">
        <span className="pill">{modo === 'ti' ? 'Radar TI (opcional)' : 'Lista geral'}</span>
      </div>

      <div className="topbar__search">
        <input
          type="search"
          placeholder="Buscar objeto, órgão ou município…"
          value={busca}
          onChange={(e) => onBusca(e.target.value)}
          aria-label="Buscar oportunidades"
        />
      </div>

      <button
        type="button"
        className="btn btn--ghost topbar__menu-toggle"
        aria-expanded={menuOpen}
        aria-controls="topbar-actions"
        onClick={() => setMenuOpen((o) => !o)}
      >
        {menuOpen ? 'Ocultar filtros' : 'Filtros'}
      </button>

      <div
        id="topbar-actions"
        className={`topbar__actions ${menuOpen ? 'topbar__actions--open' : ''}`}
      >
        <label className="topbar__period">
          <span className="sr-only">Modo de visualização</span>
          <select
            value={modo}
            onChange={(e) => {
              const m = e.target.value as ModoLista;
              onModo(m);
              if (m === 'ti') onNicho('ti_software');
              if (m === 'geral' && nicho === 'ti_software') onNicho('todos');
            }}
            aria-label="Modo de visualização"
          >
            <option value="geral">Todos os setores (dados coletados)</option>
            <option value="ti">Radar TI</option>
          </select>
        </label>

        <label className="topbar__period">
          <span className="sr-only">UF</span>
          <select
            value={escopoUf}
            onChange={(e) => onEscopoUf(e.target.value as EscopoUf)}
            aria-label="Filtro de UF"
          >
            <option value="config">{rotuloColeta(ufsConfig)}</option>
            {ufsSelect.map((uf) => (
              <option key={uf} value={uf}>
                {uf}
              </option>
            ))}
            <option value="todas">Todas</option>
          </select>
        </label>

        <label className="topbar__period">
          <span className="sr-only">Nicho</span>
          <select
            value={modo === 'ti' ? 'ti_software' : nicho}
            onChange={(e) => {
              const v = e.target.value as NichoFiltro;
              onNicho(v);
              if (v !== 'todos' && v !== 'ti_software' && modo === 'ti') onModo('geral');
              if (v === 'ti_software') onModo('ti');
              if (v === 'todos') onModo('geral');
            }}
            aria-label="Filtro de nicho"
            disabled={modo === 'ti'}
          >
            <option value="todos">Todos</option>
            {nichoOpcoes.map((n) => (
              <option key={n.id} value={n.id}>
                {n.label} ({n.count})
              </option>
            ))}
          </select>
        </label>

        <label className="topbar__period">
          <span className="sr-only">Ordenação</span>
          <select
            value={ordenacao}
            onChange={(e) => onOrdenacao(e.target.value as OrdenacaoLista)}
            aria-label="Ordenação da lista"
          >
            <option value="publicacao">Publicação mais recente</option>
            <option value="prazo">Prazo de proposta (mais próximo)</option>
          </select>
        </label>

        <label className="topbar__period">
          <span className="sr-only">Período</span>
          <select
            value={prazoValue}
            onChange={(e) => onDias(parsePrazo(e.target.value))}
            aria-label="Filtro de prazo"
          >
            <option value="abertas">Abertas</option>
            <option value={7}>Prazo até 7 dias</option>
            <option value={15}>Prazo até 15 dias</option>
            <option value={30}>Prazo até 30 dias</option>
            <option value={3650}>Qualquer prazo</option>
          </select>
        </label>

        <label className="topbar__toggle">
          <input
            type="checkbox"
            checked={mostrarTestes}
            onChange={(e) => onMostrarTestes(e.target.checked)}
          />
          Mostrar registros de teste
        </label>

        <button type="button" className="btn btn--ghost" onClick={onTheme} title="Alternar tema">
          {theme === 'dark' ? '☀' : '☾'}
        </button>

        <button type="button" className="btn btn--primary" onClick={onReload} disabled={loading}>
          {loading ? 'Atualizando…' : 'Atualizar'}
        </button>
      </div>
    </header>
  );
}
