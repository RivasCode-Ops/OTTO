# OTTO — Documento de produto e roadmap

**Versão:** 1.0 · jun/2026  
**Status:** V1 técnico funcional · alinhamento estratégico pendente  
**Repositório:** [RivasCode-Ops/OTTO](https://github.com/RivasCode-Ops/OTTO)

---

## 1. O que é o OTTO

OTTO é um **radar de oportunidade em licitações públicas no Piauí**. Usa dados abertos do [PNCP](https://www.gov.br/pncp/pt-br) para capturar publicações, classificá-las por nicho, priorizá-las por score e exibir oportunidades em painel local — com visão de evoluir para ciclo completo (edital → ata → contrato).

Não é um buscador genérico. O diferencial está em **classificação de mercado**, **leitura financeira** e **acompanhamento contínuo** — camadas que as fontes oficiais não entregam prontas.

> **Limites de dados:** o OTTO não corrige limitações estruturais do PNCP (campos faltantes ou inconsistentes). Ele **reduz o atrito de leitura** e agrega histórico, nicho e score mesmo com essas imperfeições.

---

## 2. Posicionamento (decisão em aberto)

Três caminhos possíveis. **Só um deve ser o foco de cada versão.**

| Caminho | Promessa | Versão alvo |
|---------|----------|-------------|
| **A. Radar de oportunidade** | “Mostro o que importa, priorizado, no seu nicho.” | **V1** |
| **B. Inteligência de compras** | “Mostro padrão de compra por órgão, nicho e recorrência.” | V2 |
| **C. Monitor de ciclo completo** | “Acompanho edital → ata → contrato → aditivo.” | V3 |

**Decisão recomendada para fechar V1:** posicionar OTTO como **radar de oportunidade (A)**. V2 e V3 ampliam escopo sem reescrever o miolo.

---

## 3. Fontes de dados

| Fonte | Papel | Status |
|-------|-------|--------|
| **PNCP** | Base oficial — editais, atas, contratos, PCA ([API pública](https://pncp.gov.br/api/pncp/swagger-ui/index.html)) | Implementado (consulta v1) |
| **TCE-PI** | Contexto local — Licitações Web, Contratos Web, Obras Web ([IN 02/2026](https://www.tcepi.tc.br/instrucao-normativa-n-o-02-de-12-de-fevereiro-de-2026/)) | Planejado (V2–V3) |

Escopo detalhado por URL e camada: **[ESCOPO-FONTES.md](./ESCOPO-FONTES.md)**.

Consultas PNCP de leitura **não exigem cadastro**. API de manutenção (escrita) fica fora do escopo até integração bidirecional.

---

## 4. Estado atual do produto

### O que já funciona (V1 técnico)

| Capacidade | Detalhe |
|------------|---------|
| Coleta PNCP | Paginação completa, retry, log de execução (`otto ingest`) |
| Normalização | Schema estável + `raw_json` para reprocessamento |
| Persistência | SQLite, upsert por `numero_controle_pncp` |
| Nicho | TI/software — keywords, confiança alta/baixa |
| Score | Fórmula configurável (`config/score.yaml`), breakdown no painel |
| Painel | KPIs, tabela priorizada, detalhe por oportunidade |
| Histórico | Parcial — eventos de mudança (situação, valor, prazo) |
| Qualidade | Mínimo — flag `qualidade_dados` |

### Status territorial e operação

- **Status territorial:** a V1 técnica rodou em **SP** para validação de coleta e painel; **a V1 de produto usa PI (`UF = PI`) por padrão** em `config/ingest.yaml`.
- **Operação:** coleta manual; sem agendamento nem alertas (fechar V1).
- **Escopo documental:** apenas editais/publicações; sem atas, contratos, PCA ou vínculos.

### O que OTTO **não** é (ainda)

- Integração TCE-PI, atas/contratos, PCA, alertas automáticos, vínculo edital→contrato, classificação por LLM, feed RSS de portais.

---

## 5. Mapa de maturidade por bloco

| Bloco | Status | Observação |
|-------|--------|------------|
| Fonte PNCP | Implementado | API consulta v1 |
| Fonte TCE-PI | Não implementado | Expansão V2–V3 |
| Ingestão recorrente | Parcial forte | Falta cron + incremental maduro |
| Normalização | Implementado | |
| Dedupe / SQLite | Implementado | |
| Nicho TI | Implementado | Outros nichos: V2 |
| Score | Implementado | Evolução: V2 |
| Painel | Implementado | Filtros avançados: V1 |
| Histórico de mudança | Parcial | Completar V1 |
| Qualidade de dados | Mínimo | Endurecer V1 |
| Edital → ata → contrato | Não implementado | V2–V3 |
| Atas / contratos / PCA | Não implementado | PNCP já publica; Otto ainda não ingere |
| Alertas | Não implementado | V1 |
| Território PI | **PI por padrão** | V1 produto alinhada; fechar ingest agendada |
| MCP / IA sobre acervo | Não implementado | V2 |
| Posicionamento final | Aberto | Fechar como radar (V1) |

---

## 6. Roadmap oficial

### V1 — Radar operacional local

**Objetivo:** operador abre o painel e **não precisa consultar o PNCP manualmente** para o pipeline do nicho principal.

| # | Entrega | Prioridade |
|---|---------|------------|
| 1 | Recorte **PI** (ou multi-UF parametrizável) | Urgente |
| 2 | Ingestão **agendada** (Task Scheduler / cron) | Alta |
| 3 | Ingestão **incremental** (`dataAtualizacaoGlobal`) | Alta |
| 4 | Camada de **qualidade** (regras, reprocessamento, flags) | Alta |
| 5 | **Alertas** básicos (novas oportunidades, mudança de status/prazo) | Média |
| 6 | Histórico mínimo **completo** | Média |
| 7 | Filtros no painel (município, modalidade, confiança) | Média |

**Critério de V1 fechada:** fila TI/PI confiável, atualizada automaticamente, com alerta quando algo relevante muda.

---

### V2 — Inteligência de compras

**Objetivo:** responder **padrão de compra e recorrência**, não só listar editais.

| Entrega |
|---------|
| Nichos configuráveis (YAML) |
| Score v2 (histórico órgão, recorrência real) |
| Dashboard por órgão, município, série temporal |
| Ingestão de **atas RP** e **contratos** |
| Cache, fallback e reconciliação quando PNCP falha |
| MCP sobre acervo local (consulta no Cursor) |
| Integração exploratória **TCE-PI** |

**Critério de V2:** “Este órgão compra TI com que frequência e ticket médio?”

---

### V3 — Monitor de ciclo completo

**Objetivo:** produto **vendável** como inteligência operacional de ponta a ponta.

| Entrega |
|---------|
| Grafo documental: contratação → ata → contrato → aditivo |
| **PCA** como sinal antecipado |
| **Obras Web** e instrumentos correlatos (TCE-PI) |
| Motor de acompanhamento (vigência, saldo ARP, aditivos) |
| Alertas multicanal e regras por cliente |
| Multi-tenant / SaaS (se modelo comercial exigir) |

**Critério de V3:** acompanhar ciclo completo com confiança operacional.

---

## 7. Riscos conhecidos

| Risco | Mitigação Otto |
|-------|----------------|
| Qualidade inconsistente no PNCP | `raw_json`, flags, reprocessamento, nunca confiar em campo único |
| Múltiplas URLs/estruturas para visão completa | Normalização + vínculos (V2–V3) |
| API instável ou lenta | Retry, backoff, cache, ingest incremental |
| Scope creep | Uma versão, um posicionamento por vez |

Referências: [Transparência Internacional — PNCP](https://www.transparencia.org.br/noticias/lift-dados-abertos-do-pncp-devem-ser-mais-acessiveis/), documentação oficial [gov.br/pncp](https://www.gov.br/pncp/pt-br).

---

## 8. Prioridade imediata (próximas sprints)

```
1. Fechar V1 PI — ingest agendada + incremental + alertas
2. Qualidade de dados
3. Abas do quadro (licitações → 4 abas)
4. Atas / contratos / TCE-PI   ← V2
```

---

## 9. Fora de escopo (por versão)

| Item | Versão mínima |
|------|---------------|
| LLM para classificação | Não prioritário |
| Multi-tenant / auth | V3+ |
| Deploy cloud | Após V1 fechada |
| Substituir SaaS-Licitacao | Produtos separados |

---

## 10. Referências técnicas

- [docs/QUADRO-OTTO.md](./QUADRO-OTTO.md) — matriz de eventos, modalidades, abas e colunas do painel
- [docs/ESCOPO-FONTES.md](./ESCOPO-FONTES.md) — core PNCP + TCE-PI vs fora de escopo
- [docs/DOMINIO-OTTO.md](./DOMINIO-OTTO.md) — entidades e fluxo
- [docs/NICHOS.md](./NICHOS.md) — taxonomia TI (MVP)
- [docs/REFERENCIAS.md](./REFERENCIAS.md) — OSS reaproveitável
- [README.md](../README.md) — instalação e uso local

---

*Documento vivo. Atualizar quando V1 for fechada ou posicionamento for decidido formalmente.*
