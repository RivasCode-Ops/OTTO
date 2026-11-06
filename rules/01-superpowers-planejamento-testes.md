# 1. Superpowers (Planejamento e Testes)

Regra base de execução para qualquer funcionalidade nova ou alteração relevante no OTTO.

## Obrigatório

1. **Plano de Execução antes do código**  
   Antes de escrever qualquer código, apresente um **Plano de Execução** com:
   - objetivo em uma frase;
   - arquivos/módulos afetados;
   - passos ordenados;
   - riscos ou decisões em aberto;
   - como validar (comando de teste ou checagem manual).

2. **Testes unitários para funcionalidades novas**  
   Sempre escreva testes unitários para novas funcionalidades:
   - Python: `packages/otto-core/tests/`
   - API/CLI: pytest no módulo correspondente;
   - Frontend: typecheck mínimo; testes quando houver infraestrutura.

3. **Refatorar padrões ruins**  
   Se encontrar padrões de design ruins no código tocado, refatore de forma **mínima e focada** — não expandir escopo além do necessário para corrigir o problema.

## Formato do Plano de Execução (template)

```markdown
## Plano de Execução

**Objetivo:** …

**Arquivos:** …

**Passos:**
1. …
2. …

**Validação:** …
```

## Exceções

- Correções triviais de typo ou documentação pura: plano pode ser de 2–3 linhas.
- Hotfix urgente: plano curto + teste de regressão obrigatório antes de fechar.
