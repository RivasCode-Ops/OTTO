# OTTO

**Radar de oportunidades em licitações públicas no Piauí** — captura dados do [PNCP](https://www.gov.br/pncp/pt-br/acesso-a-informacao/dados-abertos), classifica por nicho, prioriza por score e exibe oportunidades em painel local, com visão de evoluir para ciclo completo (edital → ata → contrato).

**Produto:** Piauí (PI) · nicho MVP **TI/software** · SQLite local · sem login.

> **Status territorial:** a V1 técnica rodou em SP para validar coleta e painel; **a V1 de produto usa PI (`UF = PI`) por padrão** em `config/ingest.yaml`.

> **Limites de dados:** o OTTO não corrige limitações estruturais do PNCP (campos faltantes ou inconsistentes). Ele **reduz o atrito de leitura** e agrega histórico, nicho e score mesmo com essas imperfeições.

---

## O que já funciona

| Peça | Descrição |
|------|-----------|
| Coleta PNCP | `otto ingest` — paginação completa, retry, log de execução |
| Persistência | SQLite, dedupe por edital, JSON bruto para reprocessar |
| Nicho | TI/software (keywords + confiança alta/baixa) |
| Score | 0–100 configurável (`config/score.yaml`) |
| Painel | KPIs, tabela priorizada, detalhe com breakdown do score |
| API | FastAPI para o dashboard |
| Windows | `INSTALAR-OTTO.bat` · `INICIAR-OTTO.bat` |
| Testes | pytest (core) + typecheck (app) |

## O que ainda não é

- Integração **TCE-PI** (Licitações Web, Contratos Web, Obras Web) — V2/V3  
- **Atas, contratos, PCA**, dispensa/inexigibilidade — V2+  
- **Alertas** automáticos — fechar V1  
- Vínculo **edital → ata → contrato** — V3  
- Classificação por **LLM** — regras determinísticas de propósito  
- RSS ou “notícias” de portais — só **eventos** derivados do PNCP (e futuro TCE-PI)

---

## Uso real (local)

**Guia completo:** [docs/INSTALACAO.md](docs/INSTALACAO.md) (instalar, abrir, coleta, encerrar, problemas).

**Requisitos:** Python 3.11+ · Node.js 18+

```bat
INSTALAR-OTTO.bat
INICIAR-OTTO.bat
```

| Serviço | URL |
|---------|-----|
| Painel (app) | http://127.0.0.1:5194 |
| API | http://127.0.0.1:8791 |

**Coletar editais (PI, pregão eletrônico):** `otto ingest --days 7` ou **Configurações → Coleta PNCP** no app.

**Critério de uso diário (V1 fechada):** abrir o painel e **não precisar** consultar o PNCP manualmente para o pipeline do nicho principal.

---

## Posicionamento

| | |
|---|---|
| **O que é** | Radar de oportunidade por nicho |
| **Território** | Piauí |
| **Nicho MVP** | TI / software |
| **Diferencial** | Score + nicho + histórico — não listagem crua |
| **SaaS-Licitacao** | Produto separado (não fundir) |

**Núcleo de fontes:** PNCP + TCE-PI (futuro). Painel de Preços, Transparência PI e CKAN setoriais ficam **fora do produto** (apoio manual).

---

## Roadmap (resumo)

| Versão | Foco |
|--------|------|
| **V1** | Radar PI — pregão, nicho TI, alertas, qualidade |
| **V2** | Inteligência — mais modalidades, atas/contratos, TCE-PI |
| **V3** | Ciclo completo — edital → ata → contrato → aditivo |

Detalhes: [docs/ROADMAP.md](docs/ROADMAP.md)

---

## Histórico de mudanças

O histórico de versões do OTTO está em [CHANGELOG.md](./CHANGELOG.md).  
Para detalhes da V1, veja também [docs/RELEASE-V1.md](./docs/RELEASE-V1.md) e o checklist operacional em [docs/CHECKLIST-FASE-A.md](./docs/CHECKLIST-FASE-A.md).

---

## Documentação

Estes arquivos existem para que **qualquer dev ou parceiro** entenda **o que o OTTO faz hoje** e **para onde vai** (PI, TCE-PI, ciclo completo):

| Documento | Conteúdo |
|-----------|----------|
| [docs/INSTALACAO.md](docs/INSTALACAO.md) | Instalar / abrir / coleta / encerrar (LICITAR na base OTTO) |
| [TECH_STACK.md](TECH_STACK.md) | Versões, comandos, portas, convenções |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Módulos, fluxos, limites entre camadas |
| [docs/RELEASE-V1.md](docs/RELEASE-V1.md) | Marco V1 operacional (jun/2026) |
| [docs/ESCOPO-FONTES.md](docs/ESCOPO-FONTES.md) | PNCP + TCE-PI vs fora de escopo |
| [docs/QUADRO-OTTO.md](docs/QUADRO-OTTO.md) | Matriz de eventos, modalidades e abas do painel |
| [docs/AGENDADOR-WINDOWS.md](docs/AGENDADOR-WINDOWS.md) | Agendar ingest diário 7h (Task Scheduler) |
| [docs/INGEST-INCREMENTAL.md](docs/INGEST-INCREMENTAL.md) | Plano ingest incremental (pós-V1) |
| [docs/CHECKLIST-QA-INTERFACE.md](docs/CHECKLIST-QA-INTERFACE.md) | QA visual do painel (15 min) |
| [docs/CHECKLIST-VALIDACAO-PI.md](docs/CHECKLIST-VALIDACAO-PI.md) | Validação dados PI vs PNCP |
| [docs/WIREFRAME-PAINEL.md](docs/WIREFRAME-PAINEL.md) | Wireframe Radar — KPIs, prioridade, tabela, drawer |
| [docs/DOMINIO-OTTO.md](docs/DOMINIO-OTTO.md) | Entidades e fluxo de dados |
| [docs/NICHOS.md](docs/NICHOS.md) | Taxonomia TI (MVP) |
| [docs/REFERENCIAS.md](docs/REFERENCIAS.md) | OSS e manuais PNCP |

---

## Repositório

https://github.com/RivasCode-Ops/OTTO

---

## Estrutura técnica

Ver [TECH_STACK.md](TECH_STACK.md) e [ARCHITECTURE.md](ARCHITECTURE.md).

```
packages/otto-core   # PNCP, nicho, score, SQLite
services/ingest      # CLI otto ingest
api/                 # FastAPI
app/                 # Dashboard React
config/              # ingest.yaml, score.yaml
rules/               # Time 6-in-1 — rules/00-ai-engineering-team.md
```
