# 2. Frontend Design (Qualidade UI/UX)

Regra para componentes e telas do painel OTTO (`app/`).

## Stack visual do projeto

| Camada | Tecnologia |
|--------|------------|
| UI | React 19 + TypeScript + Vite |
| Estilo | **CSS customizado** — `app/src/styles.css` (variáveis `--accent`, `--bg-*`, etc.) |
| Tipografia | **DM Sans** (Google Fonts, `index.html`) |
| Referência de produto | `docs/WIREFRAME-PAINEL.md` |

Não usar Tailwind, Shadcn ou libs de UI externas **sem decisão explícita** — manter consistência com o design system existente.

## Obrigatório ao criar componentes

1. **Estilos no design system**  
   - Reutilizar classes e tokens de `styles.css` (`.kpi-card`, `.priority-card`, `.score-badge`, `.drawer`, etc.).  
   - Novos tokens via variáveis CSS em `:root` / `[data-theme='dark']`, não valores soltos repetidos.

2. **Acessibilidade**  
   - Labels em inputs (`aria-label` ou `<label>` visível).  
   - Botões icon-only com `aria-label`.  
   - Drawer/modal: `role="dialog"`, `aria-labelledby`, foco e fechamento óbvio (×, backdrop, Esc quando aplicável).  
   - Estados de loading: `aria-busy` ou texto “Carregando…”.

3. **Responsividade**  
   - Layout testável em ≥320px (sidebar some em mobile; grids colapsam).  
   - Tabela com `overflow-x: auto` quando necessário.  
   - Touch targets ≥ 44px em controles clicáveis.

4. **Hierarquia visual**  
   - Três bandas: contexto/ação (topbar) → leitura executiva (KPIs) → decisão (prioridade) → exploração (tabela).  
   - Espaçamento consistente (`gap`, padding de cards, `--radius`).  
   - Cor com **função semântica**: teal = ação/foco, âmbar = urgência, neutro = secundário.

5. **Evitar design genérico**  
   - Não “SaaS template” azul genérico.  
   - Não listagem crua sem KPIs/prioridade quando for tela principal.  
   - Empty states e skeletons — nunca tela em branco ou só “Carregando…”.

## Estrutura de arquivos

```
app/src/
  components/     # um componente por arquivo, PascalCase
  styles.css      # design system global
  utils.ts        # helpers de UI (score, datas, filtros)
```

## Checklist antes de merge

- [ ] Typecheck: `npm run typecheck --prefix app`
- [ ] Contraste legível em dark e light (`data-theme`)
- [ ] Nenhum texto crítico só por cor (ícone + label)
- [ ] Componente alinhado ao wireframe quando existir

## Exceções

- Protótipo descartável: avisar no PR/plano; não misturar com design system principal.
