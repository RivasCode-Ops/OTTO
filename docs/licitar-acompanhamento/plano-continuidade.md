# Plano de continuidade — lotes (proposta)

**Status:** propostas. **Não iniciar** lotes de funcionalidade sem aprovação explícita.  
**Fonte canônica dos estados:** `dados.json` → `plano_lotes[]`.

## L0 — Diagnóstico + painel (esta etapa)

- **Objetivo:** mapa OTTO×LICITAR + acompanhamento local  
- **Estado:** concluída (evidência em `dados.json` / pytest 13 passed)  
- **Sem** alteração de negócio em core/API/app de oportunidades

## L1 — Defaults de descoberta (proposta; **não autorizado**)

Base OTTO e stack: **já decididas** (não são pendências do L1).

| Campo | Conteúdo |
|-------|----------|
| Objetivo | Alinhar lista ao §3/§6.3 sem remover radar TI |
| Requisitos | R-03, R-06.2, R-06.3 |
| Aproveita | API, `app` filtros, score/niche como modo opcional |
| Alterações previstas | Defaults de listagem; docs score vs ordenação objetiva |
| Riscos | Regressão do uso diário TI |
| Aceite | Lista sem perfil; TI removível se decidido; pytest + typecheck; radar TI acessível |
| Bloqueia este escopo | **D-nicho-default**, **D-score-licitar** |
| Não bloqueia L1 | D-fonte, D-abrangencia (salvo se L1 mudar UF), D-ia, D-formatos-docs, D-multiuser, D-backup |

## L2 — Interesse e estados do usuário

Persistência + API + ações no detalhe (salvar/analisar/rejeitar/decidir), sem análise documental completa.  
**Riscos:** migração SQLite em DB operacional; POST/CORS.  
**Deps:** L1 + D-multiuser.

## L3 — Documentos e análise com evidências

Entidades Documento/Análise/Evidência; importação; regras §8/§16.  
**Deps:** D-ia, D-formatos-docs.

## L4 — Checklist de preparação (§10)

Após L2/L3.

## L5 — Backup/restauração e docs de instalação (§15.5)

**Deps:** D-backup. Teste em DB temporário, nunca overwrite cego de `data/otto.db`.

## L6 — Financeiro e resultados (Fase 2 README)

R-11, R-13. Só após MVP Fase 1 estável.

## Ordem de dependência

```text
L0 ✓ → decisões humanas → L1 → L2 → L3 → L4
                              ↘ L5 (pode paralelizar após L1)
L6 após Fase 1
```
