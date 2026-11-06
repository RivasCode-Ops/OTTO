# QUADRO OTTO — Matriz de eventos e modalidades monitoradas

**Tipo:** especificação de produto (painel + eventos)  
**Versão:** 1.0 · jun/2026  
**Base:** [PNCP](https://www.gov.br/pncp/pt-br) — PCA, editais, avisos, atas, contratos  
**Território alvo:** Piauí (PI)

> **Origem dos eventos:** o quadro **não traz RSS de portais** nem feed genérico de “notícias”. Cada linha é um **evento derivado do PNCP** (e, no futuro, do **TCE-PI**) — publicação nova, mudança de prazo ou de situação.

---

## 1. Objetivo

O quadro organiza **publicações e mudanças relevantes** por tipo de contratação, modalidade e estágio — **painel de fatos novos** filtrados para decisão comercial.

Cada linha responde: *o que apareceu, de que tipo, para qual nicho, com qual prazo e prioridade*.

Documentos relacionados:

- [ESCOPO-FONTES.md](./ESCOPO-FONTES.md) — o que integrar vs fora de escopo  
- [ROADMAP.md](./ROADMAP.md) — V1 radar → V2 inteligência → V3 ciclo completo  
- [NICHOS.md](./NICHOS.md) — taxonomia (MVP: TI)

---

## 2. Tipos monitorados (categorias PNCP)

| Categoria | O que é | Versão OTTO | Endpoint / origem |
|-----------|---------|-------------|-------------------|
| **Planejamento** | PCA — Plano de Contratações Anual | V2–V3 | PNCP API consulta PCA |
| **Licitação** | Editais e avisos de licitação | **V1** | `contratacoes/publicacao` |
| **Contratação direta** | Dispensa / inexigibilidade (avisos) | V2 | PNCP avisos contratação direta |
| **Registro de preços** | Atas de RP (ARP) | V2 | PNCP atas |
| **Execução** | Contratos vigentes / empenhos | V2–V3 | PNCP contratos |

---

## 3. Modalidades — Lei 14.133/2021 (escopo principal)

**Tomada de preços e convite foram extintos** na Lei 14.133. No Otto:

- **Escopo principal:** modalidades abaixo (contratações atuais).  
- **Legado:** tomada de preços / convite só se houver base histórica explícita — **fora do MVP**.

| Modalidade | Classe | Uso típico | Cód. PNCP (ref.) | Monitorar |
|------------|--------|------------|------------------|-----------|
| **Pregão** | Licitação | Bens e serviços comuns; maior volume | 6 (eletrônico) | **Sim — V1** |
| **Concorrência** | Licitação | Obras, engenharia, casos especiais | 4 | V2 |
| **Concurso** | Licitação | Trabalho técnico, científico, artístico | 3 | V2 |
| **Leilão** | Licitação | Alienação de bens | 5 | V2 |
| **Diálogo competitivo** | Licitação | Soluções complexas | 7 | V2 |
| **Dispensa** | Contratação direta | Sem disputa aberta | (tipo aviso) | V2 |
| **Inexigibilidade** | Contratação direta | Fornecedor exclusivo | (tipo aviso) | V2 |
| **Ata de RP** | Registro de preços | Compras recorrentes, adesão | — | V2 |
| **Contrato** | Execução | Contratação efetivada | — | V2–V3 |
| Tomada de preços | Legado | Pré-14.133 | — | **Fora do escopo principal** |
| Convite | Legado | Pré-14.133 | — | **Fora do escopo principal** |

Referência modalidades: [TCU — Modalidades de licitação](https://licitacoesecontratos.tcu.gov.br/3-6-modalidades-de-licitacao/).

---

## 4. Matriz tipo × modalidade × o que monitorar

| Tipo | Modalidade / classe | O que monitorar | Filtros do quadro |
|------|---------------------|-----------------|-------------------|
| Licitação | Pregão | Bens/serviços padronizados; alto volume PI | UF, município, órgão, palavra-chave, **recebendo propostas** |
| Licitação | Concorrência | Obras, engenharia, especiais | UF, órgão, faixa valor, objeto, prazo |
| Licitação | Concurso | Seleção técnica/artística | Palavra-chave, órgão, tema, data |
| Licitação | Leilão | Alienação de bens | Órgão, objeto, data, valor |
| Licitação | Diálogo competitivo | Contratações complexas | Alto valor, objeto complexo, órgão |
| Contratação direta | Dispensa / inexigibilidade | Fora da disputa; ainda relevante | Tipo aviso, órgão, palavra-chave, valor |
| Registro de preços | ARP | Recorrência, adesão futura | Órgão gerenciador, objeto, vigência, UF |
| Execução | Contrato | O que virou contratação efetiva | Fornecedor, órgão, vigência, valor, status |
| Planejamento | PCA | Intenção futura de compra | Órgão, exercício, categoria, previsão |

---

## 5. Colunas do quadro (modelo de dados / UI)

| Coluna | Campo Otto | Função |
|--------|------------|--------|
| **Evento** | `tipo_evento` | Novo edital, mudança prazo, nova ata… |
| **Categoria** | `categoria` | Licitação, direta, ata, contrato, PCA |
| **Modalidade** | `modalidade` + `modalidade_codigo` | Pregão, concorrência, dispensa… |
| **Objeto** | `objeto_compra` | Descrição da contratação |
| **Nicho** | `nicho` | TI, saúde, obras… (regras Otto) |
| **Órgão** | `orgao_razao_social` | Publicador |
| **UF / Município** | `uf`, `municipio_ibge` | Localização |
| **Valor** | `valor_total_estimado` / homologado / contratado | Conforme fase |
| **Fase** | `situacao` | A receber / recebendo / encerrado / homologado / vigente |
| **Prazo** | `data_encerramento` (ou vigência) | Data de ação |
| **Prioridade** | `score_total` + label | Alta / média / baixa (score Otto) |
| **Link** | `link_sistema_origem` | Abrir no PNCP |

---

## 6. Eventos relevantes

O painel destaca **fatos novos**, não republicação irrelevante:

| Evento | Gatilho | Versão |
|--------|---------|--------|
| Nova publicação de edital | Insert ingest | V1 |
| Aviso contratação direta | Insert ingest | V2 |
| Nova ata RP | Insert ingest | V2 |
| Contrato vigente novo | Insert ingest | V2 |
| Mudança de prazo | `oportunidade_eventos` | V1 parcial → V1 fechada |
| Mudança de situação | `oportunidade_eventos` | V1 parcial |
| Publicação em órgão watchlist | Filtro + alerta | V2 |

Filtros combináveis: modalidade, nicho, órgão, UF/município, status, faixa valor, palavra-chave.

---

## 7. Estrutura do painel (4 abas)

| Aba | Conteúdo | Versão |
|-----|----------|--------|
| **1. Licitações ativas** | Pregão, concorrência, concurso, leilão, diálogo competitivo | V1 (só pregão) → V2 (todas) |
| **2. Contratação direta** | Dispensa, inexigibilidade | V2 |
| **3. Atas e contratos** | ARP vigentes, contratos | V2–V3 |
| **4. Planejamento** | PCA, sinais futuros | V2–V3 |

**V1 atual:** uma aba unificada equivalente à **aba 1 (pregão PI + nicho TI)** — evolui para as 4 abas conforme ingest amplia tipos.

---

## 8. Modelo resumido (exemplos PI)

| Evento | Modalidade | Órgão | Objeto | Nicho | Cidade | Valor | Prazo | Situação |
|--------|------------|-------|--------|-------|--------|-------|-------|----------|
| Novo edital | Pregão | Prefeitura X | Notebooks | TI | Teresina | R$ … | 20/06 | Recebendo propostas |
| Novo edital | Concorrência | Prefeitura Y | Reforma escola | Obras | Picos | R$ … | 25/06 | A receber propostas |
| Aviso novo | Dispensa | Órgão Z | Link internet | TI | Parnaíba | R$ … | 18/06 | Publicado |
| Nova ata | ARP | Órgão W | Medicamentos | Saúde | Floriano | R$ … | até XX | Vigente |
| Novo contrato | Contrato | Órgão K | Manutenção sistemas | TI | Teresina | R$ … | até XX | Vigente |

---

## 9. Mapeamento implementação (código)

| Spec quadro | Onde no Otto hoje | Gap |
|-------------|-------------------|-----|
| Categoria licitação | `oportunidades` via publicacao | Só editais/publicação |
| Modalidade pregão | `config/ingest.yaml` modalidade 6 | Outras modalidades V2 |
| Nicho TI | `otto_core/niche.py` | Outros nichos V2 |
| Score / prioridade | `otto_core/score.py` | — |
| Eventos | `oportunidade_eventos` | Completar tipos de evento |
| Abas painel | `app/src/App.tsx` | 4 abas V2 |
| UF PI | `config/ingest.yaml` | **PI por padrão (V1 produto)** |

---

## 10. Prioridade de entrega do quadro

```
V1 fechada
  └── Aba licitações (pregão PI) + colunas core + eventos prazo/situação

V2
  └── + modalidades licitatórias
  └── + aba contratação direta
  └── + aba atas/contratos (início)
  └── + filtros município, faixa valor, watchlist órgão

V3
  └── + aba PCA
  └── + vínculo edital → ata → contrato na mesma linha lógica
```

---

## 11. Fora do quadro principal

- Tomada de preços / convite (legado), salvo projeto histórico explícito  
- RSS de portais, mídia ou “notícias” sem evento acionável  
- Painel de Preços TCE-PI, Transparência PI — [apoio manual](./ESCOPO-FONTES.md)  

---

*Quadro oficial do Otto. Evolução do painel React deve seguir as abas e colunas deste documento.*
