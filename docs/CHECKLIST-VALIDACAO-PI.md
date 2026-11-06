# Checklist — validação OTTO em PI

Use este roteiro sempre que mudar `config/ingest.yaml`, normalização ou score.

---

## 1. Ingestão

```bat
cd OTTO
.\.venv\Scripts\otto ingest --days 7
INICIAR-OTTO.bat
```

**Esperado:** `total_bruto` > 0, `ufs=PI`, `erros=0`. Segunda execução na mesma janela: `0 novos`, N `atualizados`, sem duplicar linhas.

**Script rápido:**

```bat
.\.venv\Scripts\python scripts\validate-pi.py
```

---

## 2. Olho no olho — PNCP

Portal: [Editais e Avisos](https://pncp.gov.br/app/editais)

### 2.1 Conferir edital específico (5–10 amostras)

1. No painel OTTO (`http://127.0.0.1:5194`), anote de uma linha TI:
   - `numero_controle_pncp`
   - órgão, município, valor, prazos, situação
2. No PNCP: UF = **Piauí**, busque por ID PNCP ou palavra do objeto.
3. Campos que devem bater: objeto, valor estimado, datas, modalidade, situação.

**Script automático (3 amostras fixas):**

```bat
.\.venv\Scripts\python scripts\crosscheck-pncp.py
```

Todos os campos de negócio devem sair `[OK]`. Diferença só de formato em `data_encerramento` (espaço vs `T`) é cosmética.

### 2.2 Território PI

No painel/API (`uf=PI`):

- Nenhum registro com UF ≠ PI
- Municípios IBGE esperados (ex.: `2211001` Teresina, `2207702` Parnaíba, `2208007` Picos)

> **Nota:** se rodou ingest SP antes, o SQLite pode ter linhas SP legadas. O painel filtra `uf=PI`; para limpar: apagar `data/otto.db` e reingestir.

---

## 3. Score — leitura humana

Escolha 3–5 oportunidades TI com scores diferentes. Para cada uma, abra no PNCP e pergunte:

- “Faz sentido estar no topo?”
- “Score baixo = menos interessante?”

**Referência de score** (`config/score.yaml`): valor (40%) + urgência/prazo (30%) + nicho (20%) + recorrência órgão (10%).

**Atenção conhecida (jun/2026):** keywords amplas geram falsos positivos TI (ex.: mobiliário, medicamentos com “Portal de Compras”). Priorizar linhas com `confianca_classificacao=alta` até endurecer `NICHOS.md`.

---

## 4. Eventos (histórico)

```bat
otto ingest --days 7
otto ingest --days 7
```

**Esperado na 2ª rodada:**

| Métrica | Esperado |
|---------|----------|
| Novos | 0 (mesma janela) |
| Atualizados | ≈ total bruto |
| Duplicatas | 0 |
| Eventos | 0 se PNCP não mudou; >0 se situação/prazo/valor alterou |

Consulta manual:

```sql
SELECT * FROM oportunidade_eventos ORDER BY detectado_em DESC LIMIT 20;
```

---

## 5. Queries manuais no PNCP (roteiro fixo)

| # | Filtro PNCP | O que validar no OTTO |
|---|-------------|------------------------|
| 1 | UF = PI, modalidade = Pregão eletrônico | Volume ~ igual ao ingest (7 dias) |
| 2 | UF = PI + município Teresina | Subconjunto aparece no painel |
| 3 | Palavra-chave “software” ou “informática” | Interseção com nicho TI |
| 4 | Órgão = Estado do Piauí | Registros PGE / secretarias |
| 5 | Situação = recebendo propostas | Prazos futuros com score urgência alto |

---

## 6. Critério “V1 PI-ready”

| Critério | Status |
|----------|--------|
| Painel/API só PI | ✅ (filtro `uf=PI`) |
| Campos batem PNCP (amostra) | ✅ crosscheck 3/3 campos negócio |
| Ingest dedupe | ✅ 2ª run: 0 novos, 96 atualizados |
| Score faz sentido | ⚠️ revisar falsos positivos nicho |
| Eventos em mudança real | ⏳ aguardar mudança PNCP ou simular |

**Veredicto atual (jun/2026):** V1 **operacionalmente fechada** após registrar e testar tarefa 7h. Próximo eixo: [INGEST-INCREMENTAL.md](./INGEST-INCREMENTAL.md).

---

## Comandos úteis

```bat
.\.venv\Scripts\python scripts\validate-pi.py
.\.venv\Scripts\python scripts\crosscheck-pncp.py
curl http://127.0.0.1:8791/api/kpis?nicho=ti_software^&uf=PI
```
