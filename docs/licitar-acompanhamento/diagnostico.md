# Diagnóstico L0 — OTTO como base do LICITAR

**Acompanhar o projeto em linguagem comum:** abra `painel.html` (fonte: `dados.json`).  
Este arquivo guarda detalhe técnico do diagnóstico; o status do dia a dia está no painel.

**Data:** 2026-11-04  
**README LICITAR utilizado:** `README.txt` (raiz do OTTO)  
**README OTTO (contexto):** `README.md`  
**Fonte estruturada:** `dados.json`

## O que foi comprovado no código

| Capacidade | Evidência | Testado nesta etapa |
|------------|-----------|---------------------|
| Coleta PNCP | `pncp_client.py`, `otto ingest`, `config/ingest.yaml` | Não (evita alterar `data/otto.db`) |
| Deduplicação | Upsert PK `numero_controle_pncp` | Indireto via código + `test_normalize_minimal` |
| Classificação TI | `niche.py` | Sim — testes `classify_*` |
| Score 0–100 | `score.py` | Sim — `test_score_range` |
| Persistência SQLite | `db.py` schema + `data/otto.db` | Schema lido; DB operacional não alterado |
| Eventos de mudança | `oportunidade_eventos` | Código lido; E2E não |
| Alertas V1 | `get_alertas`, CLI, `AlertsBanner` | Código/docs; E2E não |
| API read-only | FastAPI `api/src/otto_api/main.py` | Não (serviço não iniciado) |
| Painel radar | `app/` React | Não (typecheck/UI não executados) |
| Agendamento Windows | `AGENDAR-INGEST*.bat` | Scripts existem; Task Scheduler não verificado |

**pytest:** `13 passed` em `packages/otto-core/tests/`.

## Só documentado / não revalidado aqui

- Fluxo diário “abrir painel sem consultar PNCP manualmente” (README OTTO)
- Jobs no Task Scheduler
- Incremental Fase B (`docs/INGEST-INCREMENTAL.md`)
- Qualidade de dados PI em produção local

## Lacunas vs README LICITAR (resumo)

- Fluxo usuário (interesse, análise, decisão, checklist, financeiro): **ausente**
- Documentos / evidências / IA: **ausente**
- Descoberta multi-setor sem nicho obrigatório: **parcial** (default TI)
- Ordenação sem pontuação opaca (§6.3): **tensão** com `score_total`
- Backup/restauração UI: **ausente**
- Modelo de dados §17: **parcial**

## Tensão de produto (registrar, não resolver sozinho)

1. README LICITAR: stack pendente; independência do OTTO; integração OTTO na **Fase 4**.  
2. Instrução desta etapa: continuar **a partir do OTTO**, sem recomeçar.  
3. Decisão necessária: evolução do mesmo produto vs produto novo reutilizando pacotes.

Detalhes por requisito: ver `dados.json` → `requisitos[]` e o painel.
