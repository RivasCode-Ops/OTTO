# 7. Backend + Operação (Python, API, Ingest)

Regra para **camadas Python** (`otto-core`, ingest CLI, FastAPI) e **rotina operacional** (coleta agendada, logs, alertas).

Complementa #2 (só front), #4 (security) e #6 (QA). Leia [TECH_STACK.md](../TECH_STACK.md) e [ARCHITECTURE.md](../ARCHITECTURE.md) antes de mudanças estruturais.

## Quando aplicar

- Editar `packages/otto-core/`, `services/ingest/`, `api/`, `scripts/`, `config/`.
- Alterar classificador, score, schema SQLite, contrato REST ou fluxo PNCP.
- Configurar/debugar agendador Windows ou logs de ingest.

---

## 1. Backend — princípios

### Camadas (não inverter)

```text
otto_core  ←  única fonte de negócio + SQL
    ↑
otto_ingest / otto_api  ←  adaptadores finos
```

| Fazer | Evitar |
|-------|--------|
| Nova query em `otto_core/db.py` | SQL na API ou no CLI |
| Regra de nicho em `niche.py` | Keywords espalhadas no front |
| Modelos Pydantic em `models.py` | dict solto entre camadas |
| Type hints em funções públicas | `Any` sem necessidade |

### FastAPI (`api/`)

- Endpoints **GET** na V1; delegar ao core.
- `Query(..., ge=, le=)` em parâmetros; whitelist `uf` / `nicho` / `confianca`.
- `HTTPException(404)` genérico; fechar conexão SQLite no `finally`.
- CORS: não alargar além de `localhost:5194` sem decisão.

### CLI Click (`services/ingest/`)

- Comandos: `otto ingest`, `otto alertas`.
- Erros de item individual: logar + contador `erros`; não abortar lote inteiro por 1 falha.
- Exit code ≠ 0 quando ingest falha (`AGENDAR-INGEST.bat` depende disso).
- Mensagens stderr legíveis para operador.

### PNCP (`pncp_client.py`)

- Retry configurável (`max_retries` em `ingest.yaml`).
- Timeout explícito; tratar 5xx como transitório.
- Não duplicar chamadas na mesma janela sem motivo.

### SQLite (`db.py`)

- Sempre placeholders `?` para valores user-controlled.
- `WHERE` dinâmico: só fragmentos fixos + `params`.
- Upsert idempotente por `numero_controle_pncp`.
- Eventos derivados no upsert, não em job separado na V1.

### Testes

- Lógica nova → `packages/otto-core/tests/`.
- Rodar: `pytest packages/otto-core/tests/` antes de concluir.

---

## 2. Operação — princípios

### Fase A incremental (V1)

| Rotina | Script | Janela | Log |
|--------|--------|--------|-----|
| Diária 7h | `AGENDAR-INGEST.bat` | 2 dias | `logs/agendado.log` |
| Domingo 6h | `AGENDAR-INGEST-SEMANAL.bat` | 14 dias | `logs/agendado-semanal.log` |

Após ingest agendado: `otto alertas --hours 24` (já no `.bat` diário).

### Task Scheduler (Windows)

- **Start in:** path do OTTO **sem aspas**, **sem `\` final**.
- Ação: `AGENDAR-INGEST.bat` ou semanal; registrar via `REGISTRAR-AGENDA-*.bat`.
- Ver: [docs/AGENDADOR-WINDOWS.md](../docs/AGENDADOR-WINDOWS.md).

### Observabilidade mínima

| Sinal | Onde olhar |
|-------|------------|
| Coleta OK/falhou | `logs/agendado*.log`, tabela `ingest_runs` |
| Novos/atualizados | stdout ingest ou final do log |
| Alertas | `otto alertas`, `/api/alertas`, banner UI |
| Classificador | `python scripts/ti-summary.py` |
| Dados PI | `python scripts/validate-pi.py` |

### Falhas PNCP

- 500 intermitente: retry + monitorar logs; não “consertar” dados PNCP no OTTO.
- Ingest com `erros > 0`: investigar amostra no log antes de declarar saudável.

### Fase B (futuro)

- Skip por `dataAtualizacaoGlobal` — ver [docs/INGEST-INCREMENTAL.md](../docs/INGEST-INCREMENTAL.md).
- Não implementar Fase B até Fase A estável (3–7 ciclos nos logs).

---

## 3. Checklist antes de merge (backend/op)

```markdown
- [ ] Lógica no core, não na API/CLI
- [ ] SQL parametrizado; testes pytest passando
- [ ] Contrato REST alinhado ao TypeScript do app (se endpoint mudou)
- [ ] Exit code / logs ok para agendador
- [ ] validate-pi ou ti-summary se tocou classificador/dados PI
- [ ] DECISÃO documentada se mudou regra de negócio
```

---

## 4. Exceções

- Script one-off em `scripts/`: não virar dependência do runtime; SQL parametrizado mesmo assim.
- Spike Fase B: branch separada; não misturar com ajuste de classificador V1.

## Referências

- [TECH_STACK.md](../TECH_STACK.md) — comandos e versões
- [ARCHITECTURE.md](../ARCHITECTURE.md) — fluxos e limites
- [docs/CHECKLIST-VALIDACAO-PI.md](../docs/CHECKLIST-VALIDACAO-PI.md)
- [docs/CHECKLIST-FASE-A.md](../docs/CHECKLIST-FASE-A.md)
