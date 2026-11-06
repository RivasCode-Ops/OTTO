export type NavId =
  | 'radar'
  | 'salvas'
  | 'interesse'
  | 'prosseguir'
  | 'nao_prosseguir'
  | 'fluxo_salva'
  | 'fluxo_em_analise'
  | 'fluxo_aguardando_informacoes'
  | 'fluxo_em_preparacao'
  | 'fluxo_participacao_registrada'
  | 'fluxo_em_acompanhamento'
  | 'fluxo_encerrada'
  | 'fluxo_arquivada'
  | 'orgaos'
  | 'categorias'
  | 'regioes'
  | 'indicadores'
  | 'concorrencia'
  | 'cadastro_manual'
  | 'resultados'
  | 'configuracoes';

type Item = {
  id: NavId;
  label: string;
  hint?: string;
};

const DESCOBERTA: Item[] = [
  { id: 'radar', label: 'Lista geral' },
  { id: 'cadastro_manual', label: 'Cadastro manual' },
];

const EXPLORAR: Item[] = [
  { id: 'orgaos', label: 'Órgãos' },
  { id: 'categorias', label: 'Categorias' },
  { id: 'regioes', label: 'Regiões' },
  { id: 'indicadores', label: 'Indicadores' },
  { id: 'concorrencia', label: 'Concorrência' },
];

const ACOMP: Item[] = [
  { id: 'salvas', label: 'Salvas', hint: 'favoritas' },
  { id: 'interesse', label: 'Em interesse' },
  { id: 'prosseguir', label: 'Prosseguir' },
  { id: 'nao_prosseguir', label: 'Não prosseguir' },
  { id: 'resultados', label: 'Resultados' },
];

const FLUXO: Item[] = [
  { id: 'fluxo_salva', label: 'Salvas (fluxo)' },
  { id: 'fluxo_em_analise', label: 'Em análise' },
  { id: 'fluxo_aguardando_informacoes', label: 'Aguardando informações' },
  { id: 'fluxo_em_preparacao', label: 'Em preparação' },
  { id: 'fluxo_participacao_registrada', label: 'Participação registrada' },
  { id: 'fluxo_em_acompanhamento', label: 'Em acompanhamento' },
  { id: 'fluxo_encerrada', label: 'Encerradas' },
  { id: 'fluxo_arquivada', label: 'Arquivadas' },
];

const SISTEMA: Item[] = [{ id: 'configuracoes', label: 'Configurações' }];

type Props = {
  active: NavId;
  onNavigate: (id: NavId) => void;
  contagens?: Partial<Record<NavId, number>>;
};

function NavGroup({
  title,
  items,
  active,
  onNavigate,
  contagens,
  withCount,
}: {
  title: string;
  items: Item[];
  active: NavId;
  onNavigate: (id: NavId) => void;
  contagens?: Partial<Record<NavId, number>>;
  withCount?: boolean;
}) {
  return (
    <>
      <span className="sidebar__section">{title}</span>
      {items.map((item) => (
        <button
          key={item.id}
          type="button"
          className={`sidebar__link ${active === item.id ? 'sidebar__link--active' : ''}`}
          onClick={() => onNavigate(item.id)}
        >
          <span>{item.label}</span>
          {withCount && (
            <span className="sidebar__hint">
              {item.hint ? `${item.hint} · ` : ''}
              {contagens?.[item.id] ?? 0}
            </span>
          )}
        </button>
      ))}
    </>
  );
}

export function Sidebar({ active, onNavigate, contagens }: Props) {
  return (
    <aside className="sidebar">
      <div className="sidebar__brand">
        <span className="sidebar__mark" aria-hidden />
        <div>
          <strong>LICITAR</strong>
        </div>
      </div>

      <nav className="sidebar__nav" aria-label="Navegação principal">
        <NavGroup title="Descoberta" items={DESCOBERTA} active={active} onNavigate={onNavigate} />
        <NavGroup title="Explorar" items={EXPLORAR} active={active} onNavigate={onNavigate} />
        <NavGroup
          title="Acompanhamento"
          items={ACOMP}
          active={active}
          onNavigate={onNavigate}
          contagens={contagens}
          withCount
        />
        <NavGroup
          title="Fluxo"
          items={FLUXO}
          active={active}
          onNavigate={onNavigate}
          contagens={contagens}
          withCount
        />
        <NavGroup title="Sistema" items={SISTEMA} active={active} onNavigate={onNavigate} />
      </nav>

      <footer className="sidebar__foot">
        <span className="muted">Local · sem perfil obrigatório</span>
      </footer>
    </aside>
  );
}
