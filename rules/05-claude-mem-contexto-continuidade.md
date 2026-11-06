# 5. Claude Mem (Contexto e Continuidade)

Garantir que cada sessão (humana ou agente) **retome o projeto com o mesmo entendimento** — stack, arquitetura e motivos das decisões — sem redescobrir tudo do zero.

## Quando aplicar

- **Início** de tarefa relevante (nova feature, refactor, debug cross-módulo).
- **Fim** de tarefa que alterou stack, contratos ou regras de negócio.
- Antes de propor mudança estrutural (novo serviço, lib de UI, formato de DB).

## 1. Ler contexto canônico (ordem)

### Arquivos raiz (prioridade)

| Arquivo | Se existir, ler para… |
|---------|------------------------|
| `TECH_STACK.md` | Versões, libs, comandos, convenções de tooling |
| `ARCHITECTURE.md` | Módulos, fluxos de dados, limites entre camadas |

> **OTTO:** arquivos na raiz do repo — [TECH_STACK.md](../TECH_STACK.md) e [ARCHITECTURE.md](../ARCHITECTURE.md). Se desatualizados, corrigir no mesmo ciclo da mudança.

### Equivalentes OTTO (fallback)

| Documento | Conteúdo |
|-----------|----------|
| [README.md](../README.md) | Visão V1, stack resumido, comandos, limites de produto |
| [docs/ROADMAP.md](../docs/ROADMAP.md) | Fases V1→V3; o que entra / fica fora |
| [docs/QUADRO-OTTO.md](../docs/QUADRO-OTTO.md) | Eventos, modalidades, território PI |
| [docs/NICHOS.md](../docs/NICHOS.md) | Classificador TI (versões, keywords) |
| [docs/ESCOPO-FONTES.md](../docs/ESCOPO-FONTES.md) | PNCP vs TCE-PI vs fora de escopo |
| [docs/WIREFRAME-PAINEL.md](../docs/WIREFRAME-PAINEL.md) | Layout e hierarquia UI |
| [rules/README.md](./README.md) | Regras de trabalho do repositório |

Config viva (complementar, não substituir docs):

- `config/ingest.yaml` — UF, modalidade, janela
- `config/score.yaml` — pesos do score
- `.env.example` — variáveis de ambiente

## 2. Manter consistência

Ao implementar, alinhar com:

| Decisão já tomada | Não fazer sem plano |
|-------------------|---------------------|
| V1 = radar PI · TI · SQLite local | Multi-tenant SaaS no mesmo PR |
| Classificador **determinístico** (sem LLM na V1) | Embutir LLM “só para testar” |
| Front: React + **CSS customizado** (`app/src/styles.css`) | Tailwind/Shadcn silenciosamente |
| Core compartilhado (`otto_core`) entre CLI, ingest e API | Duplicar lógica de nicho/score na API |
| PNCP como fonte V1; TCE-PI = V2+ | Assumir campos que o PNCP não entrega |

Se a tarefa **exigir** desviar (ex.: nova UF, Fase B incremental), atualizar doc afetado no **mesmo ciclo** ou registrar decisão pendente no Plano de Execução (regra #1).

## 3. Documentar o “porquê” no código

Comentários e docstrings servem **continuidade entre sessões**, não tutorial de sintaxe.

### O que documentar

| Situação | Onde | Exemplo |
|----------|------|---------|
| Regra de negócio não óbvia | Docstring do módulo/função | Classificador TI v2.1 — por que “hospedagem” é contextual |
| Trade-off técnico | Comentário curto acima do bloco | `# WHERE dinâmico: só fragmentos fixos; valores via ?` |
| Workaround externo | Comentário + link/issue | Retry PNCP por 500 intermitente |
| Contrato API/DB | Docstring ou tipo exportado | Formato de `score_detalhe` |
| Decisão arquitetural grande | `docs/` ou ADR | Fase B skip por `dataAtualizacaoGlobal` |

### O que não documentar

- O que o código já diz pelo nome (`count_oportunidades`).
- Histórico de chat ou justificativa pessoal longa.
- TODOs vagos — preferir issue ou item no `ROADMAP.md`.

### Formato sugerido (decisão no código)

```python
# DECISÃO (2026-05): classificador v2.1 — "portal" sozinho não marca TI;
# exige contexto de software/sistema. Ver docs/NICHOS.md § TI v2.1.
```

```typescript
/** Drawer único por edital — evita stack de modais; ver WIREFRAME § detalhe. */
```

## 4. Atualizar memória do projeto

Após mudança estrutural, **atualizar pelo menos um** destes:

1. `TECH_STACK.md` ou `ARCHITECTURE.md` (quando existirem).
2. README ou doc em `docs/` correspondente.
3. Comentário `DECISÃO` no ponto de extensão principal.

Criação de `TECH_STACK.md` / `ARCHITECTURE.md` é recomendada quando:

- entrar nova linguagem, framework ou serviço;
- mudar fronteiras entre `otto_core`, `api`, `ingest` e `app`;
- onboarding de terceiros passar a ser frequente.

## 5. Checklist rápido (início de sessão)

```markdown
## Contexto carregado

- [ ] Li TECH_STACK.md / ARCHITECTURE.md **ou** README + ROADMAP + doc do domínio
- [ ] Sei UF/nicho/escopo da tarefa (PI · TI · V1?)
- [ ] Identifiquei módulos tocados sem violar limites do ROADMAP
```

## 6. Checklist rápido (fim de sessão)

```markdown
## Continuidade

- [ ] Decisões não óbvias documentadas no código ou em docs/
- [ ] Docs desatualizados corrigidos (se stack/arquitetura mudou)
- [ ] Próximo passo claro para quem abrir o repo amanhã
```

## Exceções

- Fix trivial (typo, formatação): leitura de arquitetura opcional.
- Spike descartável: marcar no código/README como experimental; não poluir docs permanentes até validar.
