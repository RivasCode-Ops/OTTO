# OTTO V1 – visão rápida

Este documento contém o resumo de apresentação da V1 do OTTO, pensado para ser usado em slides, e-mails e mensagens internas.

---

## Slide único – 4 blocos

### O que é
Radar operável de oportunidades de TI no Piauí.

### O que faz
Coleta PNCP, classifica por confiança, calcula score e exibe em painel local.

### Como acompanhar
Painel em `http://127.0.0.1:5194`; sinais de problema vão para `CHECKLIST-FASE-A.md`.

### Próximos passos
Fase A estabiliza a operação; Fase B entra só depois da linha estável.

---

## Versão resumida para e-mail / Slack

OTTO V1 é um radar de oportunidades de TI no Piauí: coleta PNCP diariamente, classifica por confiança e exibe em um painel local, sem precisar abrir o PNCP manualmente. Alertas saem por CLI, API e UI. **Como usar:** abra `http://127.0.0.1:5194` e acompanhe os KPIs; se algo estranho acontecer (erro, travamento ou dado esquisito), veja `CHECKLIST-FASE-A.md`. A Fase A valida operação; a Fase B entra depois que essa rotina estiver estável. Mais detalhes em `RELEASE-V1.md`.

---

## Documentação de referência

- [RELEASE-V1.md](./RELEASE-V1.md) — detalhes técnicos e contexto da V1
- [CHECKLIST-FASE-A.md](./CHECKLIST-FASE-A.md) — como operar e monitorar no dia a dia
- [CHANGELOG.md](../CHANGELOG.md) — histórico de versões
