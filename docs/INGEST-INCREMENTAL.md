# OTTO — Plano de ingest incremental

**Objetivo:** coleta diária mais rápida e leve, sem perder novidades nem mudanças de prazo/situação.  
**Pré-requisito:** V1 operacional (ingest agendada + dedupe + eventos).

---

## Situação hoje

| Modo | Comportamento |
|------|----------------|
| `otto ingest --days 7` | Rebusca **toda** janela PI · pregão · 7 dias |
| Upsert | Atualiza se mudou; gera eventos em `_diff_events` |
| Agendador | Mesmo fluxo 7d todo dia às 7h |

Funciona, mas **repete trabalho**: ~96 itens/dia reprocessados mesmo sem alteração no PNCP.

---

## Estratégia em 2 fases

### Fase A — Quick win ✅ implementada

**Janela adaptativa no agendador** (sem mudar core de persistência):

| Execução | Script | Janela |
|----------|--------|--------|
| Diária 7h | `AGENDAR-INGEST.bat` | `--days 2` |
| Domingo 6h | `AGENDAR-INGEST-SEMANAL.bat` | `--days 14` |

Registrar: `REGISTRAR-AGENDA-7H.bat` + `REGISTRAR-AGENDA-DOMINGO.bat`

**Critério de pronto A:** ingest diária mais rápida que 7d; reconciliação semanal sem perdas relevantes.

**Medir 3–7 dias:** tempo da ingest, volume processado, diff na reconciliação domingo.

### Monitoramento Fase A (3–7 dias)

Observar nos logs, não em um único benchmark:

| Sinal | Onde | Esperado |
|-------|------|----------|
| Tempo diário | `logs\agendado.log` | Bem abaixo da janela 7d (~10–20s vs ~90s+) |
| Volume diário | linha `Coleta concluída: N bruto` | ~20–40 itens (flutua); << 96 da janela 7d |
| Erro HTTP 500 | mesmo log | Isolado = ruído PNCP; retry no dia seguinte |
| Reconciliação | `logs\agendado-semanal.log` domingo | Total ≈ cobertura 14d; sem “buracos” vs painel |

**Fase A validada quando:** 2d consistentemente rápidos + domingo 14d sem perdas relevantes → partir para Fase B.

```bat
REM checagem rápida dos logs
findstr "Coleta concluida ERRO OK" logs\agendado.log
findstr "Coleta concluida" logs\agendado-semanal.log
```

---

### Fase B — Incremental real (2–3 PRs)

Usar `dataAtualizacaoGlobal` do PNCP (já vem no `raw_json`).

#### 1. Persistir watermark

Nova tabela `ingest_state`:

```sql
CREATE TABLE ingest_state (
  chave TEXT PRIMARY KEY,   -- ex: 'PI:6'
  ultima_coleta_em TEXT,
  ultima_atualizacao_global TEXT
);
```

Nova coluna em `oportunidades`:

```sql
ALTER TABLE oportunidades ADD COLUMN data_atualizacao_global TEXT;
```

Normalizar em `normalize_pncp_item()` a partir de `raw.dataAtualizacaoGlobal`.

#### 2. Modo CLI

```bat
otto ingest --incremental    # default após Fase B
otto ingest --full --days 7  # reconciliação explícita
```

#### 3. Regra de processamento

```
PARA cada item da API (janela curta: max(2, dias_desde_ultima_run)):
  SE item novo → upsert + evento "nova"
  SENÃO SE dataAtualizacaoGlobal > armazenada → upsert + diff eventos
  SENÃO → pular (skip_count++)
```

A API pública de **consulta** filtra por `dataInicial`/`dataFinal` (publicação), não por atualização. Por isso:

- **Janela mínima 2–3 dias** continua necessária (captura republicações/atualizações recentes).
- O ganho está em **pular upsert/score** quando `dataAtualizacaoGlobal` não mudou.

#### 4. Fallback

Se `ingest_state` vazio ou `--full`:

```bat
otto ingest --full --days 7
```

#### 5. Log / métricas

Registrar em `ingest_runs`:

- `total_bruto`, `total_pulados`, `total_atualizados`, `total_novos`

---

## Critério de “incremental pronto”

| Teste | Esperado |
|-------|----------|
| 2 ingest incremental seguidos (< 1h) | 2º run: `pulados` ≈ total, `novos` = 0 |
| Alteração simulada no PNCP | 1 registro em `oportunidade_eventos` |
| `--full --days 7` semanal | Mesmo total de oportunidades que modo antigo |
| `AGENDAR-INGEST.bat` | Usa `--incremental` por padrão |
| Tempo 2º run | Claramente menor que 1º (meta: < 50% do tempo) |

---

## Ordem de implementação

```
1. ~~Fase A — AGENDAR-INGEST --days 2 + domingo --days 14~~ ✅
2. Coluna data_atualizacao_global + ingest_state
3. upsert: skip se global igual
4. CLI --incremental / --full
5. Métricas pulados no log e ingest_runs
6. Atualizar AGENDAR-INGEST + docs
```

---

## Fora de escopo (V2)

- Endpoint PNCP de manutenção (escrita)
- Incremental por `dataAtualizacaoGlobal` como **filtro de API** (se PNCP expuser na consulta v2)
- Multi-UF paralelo

---

## Referências

- [Manual integração PNCP 2.4](https://www.gov.br/pncp/pt-br/pncp/manuais/manual-de-integracao-2-4.pdf) — `dataAtualizacaoGlobal`
- Código: `pncp_client.py`, `db.upsert_oportunidade`, `services/ingest/cli.py`
- [AGENDADOR-WINDOWS.md](./AGENDADOR-WINDOWS.md)
