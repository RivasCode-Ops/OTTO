# OTTO — Architecture

Mapa de **módulos, fluxos e limites** entre camadas. Complementa [TECH_STACK.md](TECH_STACK.md) e [docs/DOMINIO-OTTO.md](docs/DOMINIO-OTTO.md).

**Princípio V1:** lógica de negócio no **core**; API e CLI são adaptadores finos; painel só consome REST.

**IA documental (nov/2026):** somente runtime local em loopback (Ollama). Sem nuvem/fallback externo. Detalhes: [docs/IA-LOCAL.md](docs/IA-LOCAL.md). **OCR local** (Tesseract) — [docs/OCR.md](docs/OCR.md). **DOCX** — [docs/DOCX.md](docs/DOCX.md). **Download seletivo PNCP** (whitelist `pncp.gov.br`, PDF/DOCX/TXT) — [docs/DOWNLOAD-ANEXOS.md](docs/DOWNLOAD-ANEXOS.md).

---

## Visão geral

```text
                    ┌─────────────────────────────────────┐
                    │           PNCP (HTTP API)            │
                    └─────────────────┬───────────────────┘
                                      │
                    ┌─────────────────▼───────────────────┐
                    │  services/ingest  (CLI: otto ingest)   │
                    └─────────────────┬───────────────────┘
                                      │
┌──────────────┐    ┌─────────────────▼───────────────────┐    ┌──────────────┐
│  config/     │───▶│      packages/otto-core              │◀───│  scripts/    │
│  ingest.yaml │    │  pncp · normalize · niche · score   │    │  validate-*  │
│  score.yaml  │    │  models · db (SQLite)                │    └──────────────┘
└──────────────┘    └─────────┬───────────────┬─────────────┘
                              │               │
              ┌───────────────▼───┐   ┌───────▼──────────────┐
              │  api/ (FastAPI)   │   │  data/otto.db        │
              │  REST read-only   │   │  oportunidades       │
              └─────────┬─────────┘   │  eventos · runs      │
                        │             └──────────────────────┘
              ┌─────────▼─────────┐
              │  app/ (React)     │
              │  Radar dashboard  │
              └───────────────────┘
```

---

## Monorepo — responsabilidades

| Path | Responsabilidade | Não deve |
|------|------------------|----------|
| `packages/otto-core` | PNCP client, normalização, classificador TI, score, SQLite, alertas | Importar FastAPI, React ou Click |
| `services/ingest` | CLI `otto ingest`, `otto alertas`; orquestra coleta | Duplicar regras de nicho/score |
| `api` | Endpoints HTTP, serialização JSON, CORS | Lógica SQL ou classificação inline |
| `app` | UI radar: KPIs, prioridade, tabela, drawer, alertas | Acessar SQLite diretamente |
| `config` | UF, modalidades, pesos de score | Código executável |
| `scripts` | Validação manual/operacional (dev) | Ser dependência de runtime |
| `docs` | Produto, wireframe, checklists | Substituir este arquivo para stack |

---

## Fluxo: ingest

1. Orquestração em `otto_core.ingest_store` (CLI `otto ingest` e `POST /api/ingest` na UI).
2. Lê `config/ingest.yaml` (27 UFs, modalidade 6, retries); UI pode override `--days` / `uf`.
3. `PncpClient` pagina API PNCP na janela de dias (1–30).
4. Cada item bruto → `normalize_pncp_item` → `classify_nicho` → `compute_score`.
5. `upsert_oportunidade` persiste + detecta eventos (mudança situação/valor/prazo).
6. `ingest_runs` registra métricas; só uma coleta com `finalizado_em` NULL por vez.

**Chave de dedupe:** `numero_controle_pncp`.

**Incremental V1 (Fase A):** janelas curtas (`--days 2` diário, `14` semanal; UI: 2/7/14).  
**Fase B (planejada):** skip por `dataAtualizacaoGlobal` — ver [docs/INGEST-INCREMENTAL.md](docs/INGEST-INCREMENTAL.md).

---

## Fluxo: painel

1. React fetch → `http://127.0.0.1:8791/api/*`.
2. Endpoints delegam a funções em `otto_core.db` (`kpis`, `list_oportunidades`, `get_alertas`, …).
3. Resposta JSON → componentes (`KpiStrip`, `PriorityCards`, `OportunidadesTable`, `DetailDrawer`).

**Contrato:** tipos espelhados em `app/src` (TypeScript) e `otto_core.models` (Pydantic). Alterar um lado exige alinhar o outro.

---

## Módulos do core

| Módulo | Função |
|--------|--------|
| `pncp_client.py` | HTTP, paginação, retry, timeout |
| `normalize.py` | JSON PNCP → campos OTTO |
| `niche.py` | Classificador TI v2.1 (determinístico) |
| `score.py` | Score 0–100 (`config/score.yaml`) |
| `models.py` | Pydantic: `Oportunidade`, eventos, score detalhe |
| `db.py` | Schema, upsert, queries, KPIs, alertas |
| `config.py` | Paths, `load_yaml`, env vars |
| `document_store.py` | Upload/extração local PDF·DOCX·TXT |
| `download_anexos_store.py` | Listar/baixar anexos PNCP (whitelist) |
| `ocr_local.py` | OCR Tesseract para PDF sem texto |

---

## API REST (V1)

| Método | Path | Core |
|--------|------|------|
| GET | `/health` | — |
| GET | `/api/kpis` | `kpis()` |
| GET | `/api/oportunidades` | `list_oportunidades()` |
| GET | `/api/oportunidades/{numero}` | `get_oportunidade()` + `list_eventos()` |
| GET | `/api/alertas` | `get_alertas()` |
| GET | `/api/eventos/recentes` | `list_recent_eventos()` |
| GET | `/api/ingest` | `status_coleta()` |
| POST | `/api/ingest` | `iniciar_coleta_async()` (background; 409 se já em andamento) |
| GET | `/api/oportunidades/{n}/anexos-remotos` | `listar_anexos_remotos()` |
| POST | `/api/oportunidades/{n}/anexos-remotos/baixar` | `baixar_anexos()` |

V1 local: sem auth; POST de ingest/backup/IA/anexos só no loopback via CORS do painel.

---

## Persistência (SQLite)

| Tabela | Uso |
|--------|-----|
| `oportunidades` | Edital normalizado + nicho + score |
| `oportunidade_eventos` | Histórico de mudanças detectadas no upsert |
| `ingest_runs` | Log de cada execução de coleta |

Path: `OTTO_DB_PATH` ou `data/otto.db`.

---

## Operação (Windows)

```text
Task Scheduler
    ├── 7h diário  → AGENDAR-INGEST.bat (2d)  → logs/agendado.log
    └── dom 6h    → AGENDAR-INGEST-SEMANAL.bat (14d) → logs/agendado-semanal.log
```

Operador observa: logs, painel, `otto alertas`, banner de alertas na UI.

---

## Limites de produto (não violar sem plano)

| Decisão | Motivo |
|---------|--------|
| Classificador **sem LLM** | Reprodutibilidade e auditabilidade TI v2.1 |
| **PI** como default de coleta/lista; nichos multi-setor | Foco territorial; classificador local por regras |
| **SQLite local** | Simplicidade operacional V1 |
| PNCP only (TCE-PI = V2+) | Escopo documentado em [docs/ESCOPO-FONTES.md](docs/ESCOPO-FONTES.md) |
| Lista/KPIs = UFs da coleta | `escopo_uf=config` (padrão); outras UFs ficam no SQLite como histórico |
| SaaS-Licitacao **separado** | Produtos distintos |

---

## Extensão futura (onde plugar)

| Feature | Camada principal |
|---------|------------------|
| Fase B incremental | `db.py` upsert + CLI flags |
| Novo nicho | `niche.py` + `docs/NICHOS.md` |
| TCE-PI | novo client em core + ingest |
| Auth / multi-user | API middleware + deploy (pós-V1) |
| Novo endpoint | `db.py` função + `main.py` rota + componente UI |

---

## Regras de desenvolvimento

Ver [rules/README.md](rules/README.md) — especialmente #4 (security), #5 (contexto), #7 (backend + operação).
