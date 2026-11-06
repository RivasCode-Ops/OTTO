# OTTO — Alertas V1

Alertas simples para uso diário local (PI · TI alta confiança).

---

## O que dispara alerta

| Tipo | Critério |
|------|----------|
| **Nova** | Oportunidade TI **alta confiança** com `coletado_em` após última visita |
| **Mudança** | Evento em `oportunidade_eventos` (prazo, situação, valor) nos últimos 7 dias |
| **Urgente** | Alta confiança com encerramento em **≤3 dias** |

---

## CLI (terminal / agendador)

```bat
otto alertas --hours 24
otto alertas --hours 48 --uf PI --confianca alta
```

Saída exemplo:

```
Alertas OTTO · PI · confiança=alta · desde 2026-06-04T14:00
  Novas alta confiança: 2
  Mudanças (7d):        0
  Vence em ≤3 dias:     1
```

---

## API

```
GET /api/alertas?uf=PI&nicho=ti_software&confianca=alta&desde=2026-06-04T12:00:00
```

Sem `desde` → últimas **24 horas**.

---

## Painel

1. Na abertura, compara com `localStorage` (`otto-last-seen-at`)
2. Banner **Radar ativo** lista novas / mudanças / urgentes
3. **Marcar como visto** grava timestamp e esconde até próxima novidade
4. **Ativar notificações** → Notification API do browser (opcional)

---

## Agendamento Windows

Use **`AGENDAR-INGEST.bat`** (2 dias) + **`AGENDAR-INGEST-SEMANAL.bat`** (14 dias) no Agendador de Tarefas:

| Campo | Valor |
|-------|-------|
| Programa | `D:\PROJETOS\OTTO\AGENDAR-INGEST.bat` |
| Frequência | Diário, ex. 07:00 |
| Condição | “Executar mesmo se usuário não estiver conectado” (opcional) |

Fluxo: ingest 7d → `otto alertas` no log.

Abrir painel depois da coleta para ver banner + KPIs.

---

## Critério V1 fechada (alertas)

- [x] CLI `otto alertas`
- [x] API `/api/alertas`
- [x] Banner no painel + last-seen
- [x] Notificação browser opcional
- [x] Script `AGENDAR-INGEST.bat`
- [ ] Ingest incremental (próximo passo)

---

## QA rápido

1. `otto ingest --days 7`
2. Abrir painel → banner se houver novidades desde last-seen
3. Clicar **Marcar como visto** → banner some
4. `curl http://127.0.0.1:8791/api/alertas?uf=PI`

Ver também: [CHECKLIST-QA-INTERFACE.md](./CHECKLIST-QA-INTERFACE.md)
