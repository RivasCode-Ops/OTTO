# OTTO — Escopo oficial de fontes de dados

**Tipo:** decisão de arquitetura  
**Versão:** 1.0 · jun/2026  
**Princípio:** núcleo pequeno, qualidade obsessiva — não abraçar todo o universo de dados públicos do Piauí.

---

## 1. Decisão

O OTTO **não** integra todas as fontes relevantes de contratação pública. Integra um **núcleo 10/10** alinhado ao objetivo:

> **Oportunidade de negócio por nicho em licitações no Piauí.**

Tudo fora desse núcleo fica como **apoio manual**, **satélite** ou **versão futura** — anotado, mas sem automação no produto.

> **Limites de dados:** o OTTO não corrige limitações estruturais do PNCP. Ele **reduz o atrito de leitura** e agrega histórico e score mesmo com imperfeições nos dados oficiais.

---

## 2. Camadas de fontes

| Camada | Papel | Automação OTTO |
|--------|-------|----------------|
| **Core nacional** | Base federal de contratações | Sim — prioridade máxima |
| **Core local (PI)** | Ciclo documental e contexto Piauí | Sim — após PNCP estável (V2+) |
| **Apoio manual** | Conferência pontual, preço, transparência | Não — link/documentação |
| **Satélite** | Datasets setoriais, estudos, CKAN | Não — referência externa |

---

## 3. Escopo oficial — Core nacional (PNCP)

### O que entra

| Recurso | URL / endpoint | Versão OTTO | Uso |
|---------|----------------|-------------|-----|
| Portal e dados abertos | https://www.gov.br/pncp/pt-br | — | Referência institucional |
| Swagger API (integração) | https://pncp.gov.br/api/pncp/swagger-ui/index.html | V2+ | Contratos, atas, detalhes |
| **API consulta — publicações** | `GET https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao` | **V1 ✅** | Editais/avisos por UF, data, modalidade |
| App editais (validação humana) | https://pncp.gov.br/app/editais | — | Conferência manual pós-ingest |
| App contratos (validação) | https://pncp.gov.br/app/contratos | V2 | Referência para vínculo documental |
| Manual API consultas v1.0 | [Manual PNCP API Consultas](https://www.gov.br/pncp/pt-br/pncp/manuais/versoes-anteriores/ManualPNCPAPIConsultasVerso1.0.pdf) | V1 | Paginação, parâmetros |
| Manual integração 2.4 | [Manual integração PNCP](https://www.gov.br/pncp/pt-br/pncp/manuais/manual-de-integracao-2-4.pdf) | V2+ | Incremental, `dataAtualizacaoGlobal` |

### Endpoints PNCP planejados (não V1)

| Recurso | Versão | Notas |
|---------|--------|-------|
| Atas de registro de preço | V2 | Saldo, vigência — oportunidade SRP |
| Contratos / empenhos | V2 | Vínculo pós-licitação |
| PCA (Plano de Contratação Anual) | V2–V3 | Sinal antecipado |
| Itens e resultados por edital | V2 | Enriquecimento de objeto/valor |
| Documentos/anexos (PDF) | V3 | Metadados primeiro; download seletivo |

### Configuração OTTO (hoje)

- Arquivo: [`config/ingest.yaml`](../config/ingest.yaml)
- **Alvo territorial:** `PI` (Piauí) — padrão em `config/ingest.yaml` (SP usado na validação técnica inicial)
- Modalidade inicial: pregão eletrônico (código 6)

---

## 4. Escopo oficial — Core local (TCE-PI)

### O que entra (fases)

| Sistema | URL | Versão OTTO | Conteúdo |
|---------|-----|-------------|----------|
| Hub Licitações e Contratos | https://www.tcepi.tc.br/fiscalizado/sistemas/licitacoes-e-contratos/ | V2+ | Portal de sistemas |
| **Licitações Web** | (via TCE-PI / integração a definir) | V2 | Editais, SRP, adesões — contexto PI |
| **Contratos Web** | (via TCE-PI / integração a definir) | V2–V3 | Contratos, convênios, aditivos |
| **Obras Web** | (via TCE-PI / integração a definir) | V3 | Obras públicas |
| IN 02/2026 (norma) | https://www.tcepi.tc.br/instrucao-normativa-n-o-02-de-12-de-fevereiro-de-2026/ | — | Requisitos de envio; guia de escopo |

### Pré-requisitos antes de integrar TCE-PI

1. PNCP PI estável (ingest, qualidade, alertas V1)
2. Modelo de vínculo documental no Otto (edital ↔ contrato)
3. Mapeamento técnico: API/export vs scraping vs carga batch (a investigar)

**Não bloqueia V1.** TCE-PI é **core de produto**, mas **segunda onda de integração**.

---

## 5. Fora do escopo oficial (apoio manual)

Usar quando necessário; **não** virar pipeline automatizado no Otto V1/V2.

| Fonte | URL | Por que fica de fora |
|-------|-----|----------------------|
| Painel de Preços Públicos (TCE-PI) | https://www.tcepi.tc.br/tce-pi-lanca-painel-para-auxilio-na-pesquisa-de-precos-dos-procedimentos-de-contratacao/ | Problema de **formação de preço**, não radar de oportunidade |
| Portal Transparência PI | https://pidigital.pi.gov.br/app/catalog/dados | Análise macro (despesa, receita, servidores) |
| Central de Compras SEAD (estudos/PDF) | https://centraldecompras.sead.pi.gov.br/ | Material estático; sem API de produto |
| CKAN IFPI (tag PNCP) | https://dados.ifpi.edu.br/dataset/?tags=pncp | Recorte setorial; redundante com PNCP |
| CKAN TRE-PI e similares | — | Casos pontuais |

**Uso permitido:** links no painel (“conferir preço”, “ver transparência”), bookmarks operacionais, pesquisa humana.

---

## 6. Satélite — referência externa apenas

Anotar existência; **sem** issue de integração até revisão de roadmap.

| Tipo | Exemplos |
|------|----------|
| Dados abertos setoriais | IFPI, TRE-PI, outros CKAN |
| Relatórios e estudos | SEAD, TCE, órgãos de controle |
| Mídia / análises | Artigos, JOTA, Transparência Internacional |
| Ferramentas comerciais | Licinexus MCP (consulta ao vivo — complementar, não core Otto) |

Arquivo de referências OSS: [REFERENCIAS.md](./REFERENCIAS.md)

---

## 7. Matriz decisão rápida

Pergunta para cada nova fonte:

1. Ajuda a **encontrar oportunidade por nicho em PI**?  
2. Tem **API ou export estável**?  
3. Não é **redundante** com PNCP ou TCE-PI já no core?  

| Respostas | Decisão |
|-----------|---------|
| Sim / Sim / Sim | Candidata a core — priorizar na roadmap |
| Sim / Não / — | Apoio manual |
| Não / — / — | Satélite ou descartar |

---

## 8. Mapa versão × fonte

```
V1 (radar PI)
  └── PNCP consulta/publicacao (PI)
  └── Qualidade + alertas + painel

V2 (inteligência)
  └── PNCP atas + contratos + PCA
  └── TCE-PI Licitações Web + Contratos Web (início)
  └── MCP acervo local

V3 (ciclo completo)
  └── Vínculo edital → ata → contrato → aditivo
  └── TCE-PI Obras Web
  └── Alertas multicanal
```

---

## 9. Riscos assumidos

| Risco | Mitigação |
|-------|-----------|
| Qualidade inconsistente PNCP | `raw_json`, flags, reprocessamento ([Transparência Internacional](https://www.transparencia.org.br/noticias/lift-dados-abertos-do-pncp-devem-ser-mais-acessiveis/)) |
| Escopo TCE-PI amplo (IN 02/2026) | Integrar por sistema, não “tudo de uma vez” |
| Tentar 10/10 em tudo | Este documento — **core explícito, resto explícito fora** |

---

## 10. Documentos relacionados

- [ROADMAP.md](./ROADMAP.md) — V1/V2/V3 e critérios de fechamento
- [DOMINIO-OTTO.md](./DOMINIO-OTTO.md) — entidades e fluxo de dados
- [REFERENCIAS.md](./REFERENCIAS.md) — OSS e manuais técnicos

---

*Decisão registrada. Alterações exigem revisão explícita deste arquivo e do ROADMAP.*
