# OTTO — Wireframe textual · Tela principal (Radar)

**Conceito:** central tática de oportunidades · PI · TI/software  
**Versão:** 1.0 · jun/2026  
**Implementação:** `app/src/` (React)

---

## Layout geral

```
┌──────────────────────────────────────────────────────────────────────────┐
│ SIDEBAR (240px)  │  TOPBAR (altura 64px)                                 │
│                  ├──────────────────────────────────────────────────────│
│                  │  FAIXA 1 — KPIs executivos (1 linha, 5 cards)         │
│                  ├──────────────────────────────────────────────────────│
│                  │  FAIXA 2 — Prioridade agora (5 cards horizontais)      │
│                  ├──────────────────────────────────────────────────────│
│                  │  FAIXA 3 — Tabela + filtros                            │
│                  │                                                        │
│                  │                                    [DRAWER detalhe →]  │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 1. Barra superior (TopBar)

| Elemento | Comportamento |
|----------|---------------|
| Logo **OTTO** | Marca; volta ao Radar |
| Contexto | Pill `PI · TI/software` |
| Busca | Filtra objeto/órgão/município na tabela e cards |
| Período | Select: 7 / 15 / 30 dias (prazo encerramento) |
| Atualizar | Recarrega API (`reload`) |
| Tema | Toggle claro/escuro (localStorage) |

**Estado vazio busca:** “Nenhum resultado para «termo»”.

---

## 2. Coluna lateral (Sidebar)

| Item | Versão | Estado MVP |
|------|--------|------------|
| Radar | V1 | **Ativo** |
| Licitações ativas | V1 | Placeholder → Radar |
| Contratação direta | V2 | Desabilitado |
| Atas e contratos | V2 | Desabilitado |
| Planejamento | V2 | Desabilitado |
| Histórico | V1 | Placeholder |
| Regras de nicho | V1 | Link doc / futuro |
| Configurações | V1 | Placeholder |

Rodapé lateral: versão + link GitHub.

---

## 3. Faixa 1 — Leitura executiva (KPIs)

Cinco cards, número grande + rótulo curto:

| KPI | Fonte | Significado |
|-----|-------|-------------|
| Oportunidades TI | API `total` (filtro atual) | Volume no recorte |
| Alta confiança | Contagem `confianca=alta` | TI “de verdade” |
| Score médio | Média dos scores visíveis | Saúde do pipeline |
| Órgãos ativos | `distinct orgao` | Diversidade territorial |
| Vence em 7 dias | API `vencendo_7_dias` | Urgência imediata |

---

## 4. Faixa 2 — Prioridade agora

Título: **Prioridade agora** · subtítulo: “Top 5 por score · alta confiança”

Cada card largo contém:

```
┌─────────────────────────────────────────────────────────┐
│ [Score 73]  ALTA                    vence em 6 dias    │
│ Aquisição de notebooks para escolas municipais…         │
│ MUNICIPIO DE CAJUEIRO DA PRAIA · Cajueiro da Praia      │
│ R$ 984.960 · Pregão · Divulgada no PNCP                 │
│ ▸ Valor alto · Prazo curto · TI alta confiança          │
└─────────────────────────────────────────────────────────┘
```

Clique → abre drawer de detalhe.  
Se < 5 alta confiança: completar com melhor score restante (badge “baixa” visível).

---

## 5. Faixa 3 — Exploração (tabela)

**Barra de filtros:**

- Toggle `Somente alta confiança` (default: ligado)
- Ordenação: score (default) · prazo · valor

**Colunas (ordem):**

1. Score (badge colorido)
2. Confiança (pill alta/baixa)
3. Objeto (truncate 2 linhas)
4. Órgão
5. Município
6. Valor
7. Prazo (+ dias restantes)
8. Situação

Linha clicável · hover · seleção com borda teal.

**Empty states:**

- Sem ingest: CTA `otto ingest --days 7`
- Filtro restritivo: “Amplie filtros ou desative ‘somente alta confiança’”

---

## 6. Drawer de detalhe (direita)

Largura ~420px · overlay escuro · preserva contexto da lista.

```
┌─ Detalhe ─────────────────────── [×] ─┐
│ Score 73 · Alta confiança             │
│ ─────────────────────────────────────│
│ Objeto (texto completo)               │
│ ─────────────────────────────────────│
│ Por que TI?                           │
│ • Matches: notebook, ti/tic           │
│ ─────────────────────────────────────│
│ Órgão · Município · UF                │
│ Modalidade · Situação                 │
│ Publicação · Encerramento propostas   │
│ Valor estimado                        │
│ ─────────────────────────────────────│
│ Score explicado                       │
│ Valor      ████████░░ 40              │
│ Urgência   █████░░░░░ 24              │
│ Nicho      ███░░░░░░░ 20              │
│ Recorrência ██░░░░░░░░  3             │
│ ─────────────────────────────────────│
│ Histórico de mudanças (se houver)     │
│ ─────────────────────────────────────│
│ [ Abrir no PNCP ]                     │
└───────────────────────────────────────┘
```

---

## 7. Sistema visual

### Tipografia
- UI: **DM Sans** (Google Fonts)
- Números/KPI: tabular, peso 600–700
- Rótulos: 11–12px, uppercase tracking leve

### Cor (tema escuro default)
| Token | Uso |
|-------|-----|
| `--accent` teal `#14b8a6` | Ação, score alto, seleção |
| `--warn` âmbar `#f59e0b` | Prazo próximo, score médio |
| `--danger` vermelho `#ef4444` | Risco / vencido |
| `--ok` verde `#22c55e` | Confirmação |
| `--bg-base` `#0f1419` | Fundo |
| `--bg-surface` `#1a222d` | Cards |

Tema claro: mesma semântica, fundos claros.

### Componentes
- Cards: radius 12px, borda 1px sutil, sombra leve
- Badges score: pill com cor por faixa
- Pills confiança: alta = teal outline; baixa = neutro

---

## 8. Entregas de implementação

| # | Entrega | Arquivo |
|---|---------|---------|
| 1 | Mapa informação | este doc |
| 2 | Sistema visual | `app/src/styles.css` |
| 3 | Tela Radar | `App.tsx` + components |
| 4 | Drawer detalhe | `DetailDrawer.tsx` |

---

## 9. Evolução V1.1

- KPI “mudanças recentes” (endpoint eventos agregado)
- Abas laterais com ingest separado por tipo
- Mapa PI (municípios)
- Atualizar coleta → chamar CLI via API (futuro)
