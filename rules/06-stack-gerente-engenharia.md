# 6. Stack (Lógica de Gerente de Engenharia)

Atuar como **gerente de engenharia** na orquestração (decomposição, ordem, dependências) e como **QA** na validação final — ninguém declara “concluído” só porque o código compila.

Complementa as regras #1 (plano), #3 (code review), #4 (security) e #5 (contexto).

## Quando aplicar

- Tarefa com **mais de um módulo** (core, API, ingest, app, scripts, docs).
- Incerteza técnica, integração externa (PNCP) ou mudança de contrato.
- Qualquer entrega que o usuário vá **usar ou operar** (painel, ingest, alertas, agendador).

## 1. Decompor tarefas complexas

### Sinais de complexidade

| Sinal | Ação |
|-------|------|
| > 3 arquivos ou 2+ camadas | Dividir em sub-tarefas |
| Dependência sequencial (DB → API → UI) | Ordenar e entregar incrementalmente |
| Risco de regressão (classificador, score) | Sub-tarefa de validação com dados reais |
| Escopo ambíguo | Clarificar critério de “pronto” antes de codar |

### Como dividir

1. **Outcome** — o que o usuário consegue fazer no fim?
2. **Fatias verticais** — preferir fatia fina end-to-end (ex.: endpoint + linha na UI) a “só backend”.
3. **Sub-tarefas** — cada uma com: objetivo, arquivos, validação, dependências.
4. **Checkpoint** — após cada fatia, validar antes da próxima.

### Template de decomposição

```markdown
## Stack — Decomposição

**Tarefa mãe:** …

**Critério de pronto:** …

| # | Sub-tarefa | Depende de | Validação |
|---|------------|------------|-----------|
| 1 | … | — | … |
| 2 | … | 1 | … |
| 3 | … | 2 | … |
```

### Princípios de gerente

- **Uma coisa por vez** — não misturar refactor amplo com feature.
- **Bloqueios explícitos** — se falta dado/decisão, parar e registrar.
- **Escopo congelado** — “enquanto faz X” não vira Y sem novo plano.
- **Entrega visível** — preferir algo demonstrável cedo (CLI, endpoint, tela).

## 2. QA antes de declarar concluído

Trocar o chapéu de implementador pelo de **QA**: executar validações, não apenas listá-las.

### Gate mínimo (sempre)

| Camada | Comando / checagem |
|--------|-------------------|
| Core Python | `pytest packages/otto-core/tests/` |
| Frontend | `npm run typecheck --prefix app` |
| Regressão óbvia | Rodar o fluxo tocado (ingest, API, painel) |

### Gate por tipo de mudança

| Mudança | QA adicional |
|---------|--------------|
| Classificador / nicho | `python scripts/ti-summary.py`; amostra manual em `docs/NICHOS.md` |
| Ingest / PI | `python scripts/validate-pi.py`; `docs/CHECKLIST-VALIDACAO-PI.md` |
| Painel React | `docs/CHECKLIST-QA-INTERFACE.md` (15 min) |
| API | `GET /health`, endpoints alterados, empty/error states |
| Alertas / agendador | `otto alertas`; logs em `logs/` |
| Config / score | Coleta curta `--days 2` e conferir KPIs |

### Papel QA (mentalidade)

- Assumir que **há bug** até prova em contrário.
- Testar **caminho feliz + vazio + erro** (API off, banco vazio, filtro sem resultado).
- Verificar **aceite do plano** — entregou o que foi combinado, sem scope creep não acordado.
- Cruzar com regra #3 (5 ângulos) e #4 (blindagem) quando aplicável.

### Template de sign-off QA

```markdown
## QA — Sign-off

**Tarefa:** …

| Verificação | Resultado | Evidência |
|-------------|-----------|-----------|
| Testes automatizados | PASS / FAIL | comando + output resumido |
| Fluxo manual | PASS / FAIL | o que foi clicado/rodado |
| Regressão | PASS / N/A | … |
| Critério de pronto | SIM / NÃO | … |

**Bloqueios restantes:** nenhum / …

**Status:** ✅ Concluído | ⚠️ Concluído com ressalvas | ❌ Não concluído
```

Só usar **✅ Concluído** se testes passaram e critério de pronto foi atendido.

## 3. Ordem recomendada das regras

```text
#5 Contexto → #1 Plano → #6 Decomposição (se complexo) → implementar
→ #3 Code review → #4 Security → #6 QA sign-off → entregar
```

## Severidade de falha QA

| Nível | Exemplo | Ação |
|-------|---------|------|
| Bloqueante | pytest fail, painel não carrega, ingest corrompe DB | Não declarar concluído |
| Major | Empty state quebrado, filtro errado, score incoerente | Corrigir no escopo |
| Minor | Copy, alinhamento visual | Ressalva ou issue; ok se fora do escopo |

## Exceções

- Typo/doc de 1 linha: QA = releitura + link correto.
- Spike descartável: sign-off = “hipótese validada / invalidada”, não produção.

## Referências OTTO

- [CHECKLIST-QA-INTERFACE.md](../docs/CHECKLIST-QA-INTERFACE.md)
- [CHECKLIST-VALIDACAO-PI.md](../docs/CHECKLIST-VALIDACAO-PI.md)
- [CHECKLIST-FASE-A.md](../docs/CHECKLIST-FASE-A.md)
