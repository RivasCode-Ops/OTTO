# Rules — OTTO

Regras de trabalho para desenvolvimento do projeto.

## Comece aqui

**[00-ai-engineering-team.md](./00-ai-engineering-team.md)** — Role **6-in-1 + OTTO**: lista dos papéis, fluxo de aplicação, matriz por situação, template de entrega.

Cursor: `.cursor/rules/00-ai-engineering-team.mdc` (orquestrador, `alwaysApply`)

---

## Papéis (detalhe)

| # | Arquivo | Escopo |
|---|---------|--------|
| 0 | [00-ai-engineering-team.md](./00-ai-engineering-team.md) | Orquestrador — time 6-in-1 + extensões |
| 1 | [01-superpowers-planejamento-testes.md](./01-superpowers-planejamento-testes.md) | Planejamento, testes e refatoração |
| 2 | [02-frontend-design-ui-ux.md](./02-frontend-design-ui-ux.md) | UI/UX, a11y, design system CSS |
| 3 | [03-code-review-5-agentes.md](./03-code-review-5-agentes.md) | Auto-revisão em 5 ângulos ao finalizar código |
| 4 | [04-security-review-blindagem.md](./04-security-review-blindagem.md) | SQLi, XSS, CSRF, secrets, validação de inputs |
| 5 | [05-claude-mem-contexto-continuidade.md](./05-claude-mem-contexto-continuidade.md) | Contexto, docs canônicos, documentar decisões |
| 6 | [06-stack-gerente-engenharia.md](./06-stack-gerente-engenharia.md) | Decomposição de tarefas + QA sign-off |
| 7 | [07-backend-operacao.md](./07-backend-operacao.md) | Python, API, ingest, SQLite, operação Windows |
| 8 | [08-git-pr-disciplina.md](./08-git-pr-disciplina.md) | Commit/push/PR só quando pedido; diff mínimo |

## Fluxo recomendado

```text
#0 Orquestrador
  → #5 Contexto (TECH_STACK + ARCHITECTURE)
  → #1 Plano → #6 Decomposição (se complexo)
  → implementar (#2 front · #7 backend)
  → #3 Review → #4 Security → #6 QA sign-off
  → #8 Git/PR (se usuário pedir commit ou PR)
```

## Documentos canônicos (regra #5)

- [TECH_STACK.md](../TECH_STACK.md) — versões, comandos, portas
- [ARCHITECTURE.md](../ARCHITECTURE.md) — módulos e fluxos

Regras ativas no Cursor: `.cursor/rules/*.mdc`
