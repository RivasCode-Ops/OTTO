# OTTO — Release V1 (operacional)

**Marco:** jun/2026 · **Território:** Piauí (PI) · **Nicho MVP:** TI/software

---

## Em uma frase

OTTO V1 é um **radar operável de licitações TI no Piauí**: coleta PNCP, classifica com confiança, prioriza por score, exibe em painel e alerta — pronto para rotina diária local.

---

## O que entrou

| Área | Entrega |
|------|---------|
| **Dados** | Ingest PI (pregão), dedupe SQLite, crosscheck PNCP, upsert idempotente |
| **Nicho** | Classificador TI v2.1 (fortes / fracos / bloqueios, hospedagem contextual) |
| **Rotina** | Agendador Windows: diário 2d (7h) + reconciliação 14d (domingo 6h), logs |
| **Painel** | Radar: KPIs, prioridade, tabela, drawer, skeleton, empty/error, dark mode |
| **Alertas** | CLI `otto alertas`, API `/api/alertas`, banner UI + notificações opcionais |
| **Incremental** | Fase A (janela curta) — Fase B (`dataAtualizacaoGlobal` + skip) planejada |

---

## Critério “V1 pronta”

Operador abre o painel e **não precisa consultar o PNCP manualmente** para o pipeline TI/PI principal; coleta roda agendada; alertas sinalizam novidades e mudanças.

---

## Próximo (pós-observação)

1. Validar Fase A nos logs (3–7 dias)  
2. Fase B: skip por `dataAtualizacaoGlobal`  
3. V2: mais modalidades, TCE-PI, atas/contratos  

Ver: [ROADMAP.md](./ROADMAP.md) · [INGEST-INCREMENTAL.md](./INGEST-INCREMENTAL.md) · [CHECKLIST-FASE-A.md](./CHECKLIST-FASE-A.md)

---

## Próximos passos – Fase A em operação

Com a V1 operável, o foco agora é observar a rotina: ingestão diária e semanal, estabilidade do PNCP e comportamento do painel no uso real. Quaisquer ajustes de lógica (score, alertas, janelas de coleta) devem ser guiados pelos sintomas registrados em logs, `ingest_runs` e feedback de uso. A Fase B – refinamento incremental por `dataAtualizacaoGlobal` e regras mais finas – só entra depois que a Fase A mostrar linha estável em produção.
