# OTTO — Tech Stack

Documento canônico de **versões, ferramentas e comandos**. Leia antes de implementar (regra #5).

**Atualizado:** nov/2026 · **Produto:** radar nacional (27 UFs) · multi-nicho · local · IA documental local (sem nuvem)

---

## Requisitos de runtime

| Ferramenta | Versão mínima | Uso |
|------------|---------------|-----|
| Python | 3.11+ | Core, ingest CLI, API |
| Node.js | 18+ | Dashboard React (Vite) |
| Windows | 10+ | Scripts `.bat`, Task Scheduler (opcional) |
| Git | qualquer recente | Versionamento |

---

## Stack por camada

| Camada | Pacote / path | Tecnologia |
|--------|---------------|------------|
| **Core** | `packages/otto-core` | Python 3.11, Pydantic 2, httpx, PyYAML, SQLite |
| **Ingest** | `services/ingest` | Click CLI (`otto`) |
| **API** | `api` | FastAPI, Uvicorn |
| **Painel** | `app` | React 19, TypeScript 5.8, Vite 6, Vitest, ESLint 9 |
| **Estilo UI** | `app/src/styles.css` | CSS customizado + DM Sans (sem Tailwind/Shadcn) |
| **Dados** | `data/otto.db` | SQLite local (gitignored) |
| **Config** | `config/*.yaml` | ingest, score |
| **Fonte externa** | PNCP API pública | HTTPS, sem API key na V1 |

---

## Dependências Python (principais)

```text
otto-core:  httpx>=0.27, pydantic>=2.7, pyyaml>=6.0
otto-ingest: click>=8.1, otto-core
otto-api:    fastapi>=0.111, uvicorn[standard]>=0.29, otto-core
dev:         pytest>=8.0, pytest-asyncio>=0.23
```

---

## Variáveis de ambiente

| Variável | Default | Descrição |
|----------|---------|-----------|
| `OTTO_DATA_DIR` | `data/` | Pasta de dados |
| `OTTO_DB_PATH` | `data/otto.db` | Caminho do SQLite |
| `OTTO_IA_LOCAL_URL` | `http://127.0.0.1:11434` | Ollama local (somente loopback) |
| `OTTO_IA_LOCAL_MODEL` | `qwen2.5:3b` | Modelo local autorizado |
| `OTTO_IA_LOCAL_MODELS_DIR` | `data/ia-models` | Pasta sugerida para pesos (D:) |

IA documental: ver `docs/IA-LOCAL.md`. Sem fallback em nuvem. OCR local (`docs/OCR.md`). DOCX (`docs/DOCX.md`). Download seletivo PNCP (`docs/DOWNLOAD-ANEXOS.md`) — só hosts `pncp.gov.br`, PDF/DOCX/TXT.

Documentar novas vars em `.env.example`. Nunca commitar `.env`.

---

## Portas e URLs (local)

| Serviço | URL | Comando |
|---------|-----|---------|
| Painel | http://127.0.0.1:5194 | `npm run dev --prefix app` |
| API | http://127.0.0.1:8791 | `uvicorn otto_api.main:app --host 127.0.0.1 --port 8791 --app-dir api/src` |
| Health | http://127.0.0.1:8791/health | — |

CORS da API: apenas origens do painel (`5194`).

---

## Instalação e bootstrap

**Guia canônico (passo a passo + troubleshooting):** [docs/INSTALACAO.md](docs/INSTALACAO.md).

```bat
INSTALAR-OTTO.bat    REM venv + pip install -e core/ingest/api + npm app
INICIAR-OTTO.bat     REM API + painel em janelas locais
```

Manual (PowerShell):

```powershell
cd D:\PROJETOS\04_LABS\OTTO
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e "packages/otto-core[dev]" -e services/ingest -e api
npm install --prefix app
```

---

## Comandos do dia a dia

### Coleta e alertas

```powershell
otto ingest --days 7              # janela retroativa (default config: 7)
otto ingest --days 2 --uf PI      # Fase A incremental
otto alertas --hours 24 --uf PI
```

### API (dev)

```powershell
uvicorn otto_api.main:app --host 127.0.0.1 --port 8791 --reload --app-dir api/src
```

### Frontend

```powershell
npm run dev --prefix app          # :5194
npm run typecheck --prefix app
npm test --prefix app
npm run lint --prefix app
npm run build --prefix app
```

### Testes

```powershell
pytest packages/otto-core/tests/
```

### Validação operacional (scripts)

```powershell
python scripts/validate-pi.py
python scripts/ti-summary.py
python scripts/crosscheck-pncp.py
```

---

## Agendamento Windows (Fase A)

| Script | Função | Janela |
|--------|--------|--------|
| `AGENDAR-INGEST.bat` | Ingest + alertas → `logs/agendado.log` | default 2 dias |
| `AGENDAR-INGEST-SEMANAL.bat` | Reconciliação → `logs/agendado-semanal.log` | 14 dias |
| `REGISTRAR-AGENDA-7H.bat` | Cria tarefa diária 7h | — |
| `REGISTRAR-AGENDA-DOMINGO.bat` | Cria tarefa domingo 6h | — |

Ver: [docs/AGENDADOR-WINDOWS.md](docs/AGENDADOR-WINDOWS.md), [docs/INGEST-INCREMENTAL.md](docs/INGEST-INCREMENTAL.md).

---

## Convenções de código

| Área | Convenção |
|------|-----------|
| Python | Type hints em APIs públicas; `from __future__ import annotations` |
| Módulos | snake_case; pacote `otto_core`, `otto_ingest`, `otto_api` |
| SQL | Placeholders `?`; lógica em `otto_core/db.py` |
| React | Componentes PascalCase em `app/src/components/` |
| Config | YAML em `config/`; não hardcodar UF/modalidade no código |
| Decisões | Comentário `# DECISÃO (data): …` + ref `docs/` |

---

## O que não usar (V1)

- Tailwind / Shadcn / libs UI externas (sem decisão explícita)
- LLM para classificação de nicho
- PostgreSQL / multi-tenant / auth (fora do escopo V1)
- Commit de `data/*.db`, `.env`, `logs/` (gitignored)

---

## Documentos relacionados

| Arquivo | Conteúdo |
|---------|----------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Módulos e fluxo de dados |
| [README.md](README.md) | Visão de produto |
| [rules/README.md](rules/README.md) | Regras de desenvolvimento |
| [docs/DOMINIO-OTTO.md](docs/DOMINIO-OTTO.md) | Entidades de domínio |
