import { useState } from 'react';
import type { ModoLista, OrdenacaoLista } from '../api';
import type { FiltroPrazo } from '../utils';

type Props = {
  busca: string;
  onBusca: (v: string) => void;
  dias: FiltroPrazo;
  onDias: (v: FiltroPrazo) => void;
  modo: ModoLista;
  onModo: (v: ModoLista) => void;
  ordenacao: OrdenacaoLista;
  onOrdenacao: (v: OrdenacaoLista) => void;
  theme: 'dark' | 'light';
  onTheme: () => void;
  onReload: () => void;
  loading: boolean;
};

function parsePrazo(v: string): FiltroPrazo {
  if (v === 'abertas') return 'abertas';
  return Number(v);
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
  theme,
  onTheme,
  onReload,
  loading,
}: Props) {
  const [menuOpen, setMenuOpen] = useState(false);
  const prazoValue = dias === 'abertas' ? 'abertas' : String(dias);

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
            onChange={(e) => onModo(e.target.value as ModoLista)}
            aria-label="Modo de visualização"
          >
            <option value="geral">Todos os setores (dados coletados)</option>
            <option value="ti">Radar TI</option>
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
