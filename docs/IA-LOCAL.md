# IA local do LICITAR (decisão 2026-11-04; evidências 2026-11-05)

**Decisão:** análise documental por IA **somente local**. Sem nuvem, sem fallback externo.

## Equipamento

| Item | Valor |
|------|--------|
| SO | Windows 10 (10.0.19045) |
| Máquina | Dell Inspiron 5458 |
| CPU | Intel Core i3-5005U @ 2,00 GHz (2/4) |
| RAM | ~15,9 GB |
| GPU | Intel HD 5500 (sem CUDA) |

## Runtime instalado

| Componente | Valor |
|------------|--------|
| Ollama | 0.40.14 |
| Modelo | qwen2.5:3b (~1,9 GB) |
| Modelos | `D:\PROJETOS\04_LABS\OTTO\data\ia-models` |
| Bind | `127.0.0.1:11434` |
| Nuvem | não — código recusa host não-loopback |

## Regras de evidência (obrigatórias)

1. Toda sugestão aplicável exige **documento + versão + trecho** verificável no texto extraído.
2. **Página** obrigatória em PDF; em TXT pode ficar vazia.
3. Sugestão **sem** evidência confirmada = **Não confirmada** (motivo exibido) — **não** se aplica pela IA.
4. Campos com origem **`usuario` nunca são sobrescritos** pela IA (nem com flag de forçar). Para alterar, edite a ficha no fluxo manual.
5. Para registrar valor sem evidência IA, use o **fluxo manual** (origem `usuario`).
6. O sistema **não inventa** trechos. Se o modelo omitir citação, tenta **localizar** no texto do documento um recorte literal do valor; se não achar, permanece Não confirmada.

## Validação (sem mock)

### Integração — OK

Jobs, sugestões, UI (progresso/erro), apply/rejeitar, preservação `natureza=usuario`, loopback-only.

### Qualidade da extração — ACEITÁVEL COM RESSALVAS

Documento: `MANUAL-IA-PDF-E2E-05NOV-B` / PDF 4 páginas (`edital-teste-ia-multipagina.pdf`).

| Checagem | Resultado |
|----------|-----------|
| Objeto / órgão / quantidades (200) / valores (~180k) | alinhados ao edital |
| Visita técnica / garantia de proposta (ausentes no texto) | não inventados |
| Requisitos / checklist | citados; citação às vezes curta (ex. cabeçalho) — revisar |
| Relatório | `data/e2e-ia-pdf-evidencias-resultado.json` |

### Evidências verificadas — OK (com gate)

Apply bloqueado sem `referencia_confirmada`. UI: Confirmadas vs Não confirmadas. pytest `test_ia_local_analise` (8).

### Desempenho — limitado pelo hardware

| Métrica | Valor |
|---------|--------|
| Carregamento (já aquecido) | ~12,9 s |
| Análise PDF 4 págs | ~91 s |
| Consumo do modelo | **nao_medido** |
| RSS observado `llama-server.exe` | ~2,1 GB (processo; não usar só `ollama.exe` ~30 MB) |

### Testes pendentes

- **Rede fisicamente desligada** — endpoint local ≠ prova desse cenário. Não desligar rede sem procedimento seguro.

### Fechamento (2026-11-05)

- Regressão: `pytest packages/otto-core/tests/` → **43 passed**
- Fluxo análise→tarefa→evidência→reinício API: `data/e2e-ia-fluxo-completo-resultado.json`
- Cobertura parcial: status `parcial` + texto **Processados:** / **Falha na parte**
- IA indisponível: job `falhou` sem quebrar fluxo manual

## Aprendizado do histórico → prompt (autorizado 2026-11-06)

- Com ≥3 sugestões decididas (aplicar/rejeitar), a **próxima** análise local recebe um bloco `<<APRENDIZADO_LOCAL>>` no prompt do usuário (preferir/evitar chaves).
- **Não** treina pesos, **não** sobe nuvem, **não** relaxa gate de evidência nem sobrescreve `natureza=usuario`.
- Status ativo/inativo aparece em Configurações e na nota de cobertura do job.
- Código: `aprendizado_store.contexto_para_analise_ia` + injeção em `ia_analise_store._executar_job`.

## OCR (autorizado à parte — 2026-11-06)

PDF sem texto nativo: OCR local (Tesseract). Ver [OCR.md](OCR.md). Sem nuvem. A IA só analisa documentos com texto já extraído (`status_extracao=ok`).

## Fora desta autorização

Download automático de editais · troca de modelo · componentes extras · commit/push/deploy.

DOCX: autorizado à parte — ver [DOCX.md](DOCX.md).
