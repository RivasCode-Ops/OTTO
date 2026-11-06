# 3. Code Review (5 Agentes / 5 Ângulos)

Ao **finalizar** uma implementação (antes de declarar pronta), faça uma **auto-revisão** simulando cinco revisores. Registre achados no chat ou no PR; corrija problemas **críticos e médios** antes de encerrar.

## Quando aplicar

- Nova funcionalidade ou alteração relevante (não em typos de uma linha).
- Após testes passarem e antes de commit/merge.

## Os 5 ângulos

### 1. Performance

| Checar | OTTO |
|--------|------|
| Complexidade | Loops aninhados em ingest/classificador → preferir O(n) ou indexação por dict/set |
| I/O | Batch de SQLite; evitar N+1 queries na API |
| Memória | Listas gigantes em ingest — streaming/chunks quando o volume crescer |
| Frontend | `useEffect` com deps corretas; cancelar fetch no unmount; evitar re-render em listas longas |
| Rede | Timeouts e retry já usados no PNCP — não duplicar chamadas desnecessárias |

**Pergunta-chave:** “Isso escala com 10× mais editais ou 10× mais linhas na tabela?”

### 2. Legibilidade

| Checar | Critério |
|--------|----------|
| Nomes | Verbos em funções (`fetchOportunidades`), substantivos em dados (`editalId`) |
| Funções | Preferir &lt; ~40 linhas; extrair só se melhorar leitura |
| Fluxo | Early return em validações; menos aninhamento |
| Tipos | Type hints Python / TypeScript explícitos em APIs públicas |
| Comentários | Só onde a regra de negócio não é óbvia (ex.: classificador TI v2.1) |

**Pergunta-chave:** “Um dev novo entende o fluxo em 2 minutos?”

### 3. Manutenibilidade (SOLID, DRY)

| Princípio | Aplicação OTTO |
|-----------|----------------|
| **S** | Classificador em `niche.py`, ingest em CLI, HTTP em client — não misturar |
| **O** | Extender nichos/scores sem editar dezenas de `if` — dados/config quando couber |
| **D** | Depender de interfaces/abstrações (ex.: repositório SQLite), não de detalhes espalhados |
| **DRY** | Duplicação &gt; 2× → extrair helper; duplicação acidental entre API e core → centralizar no core |
| **YAGNI** | Não generalizar para “futuro SaaS” sem requisito atual |

**Pergunta-chave:** “Mudar a regra de score ou UF exige quantos arquivos?”

### 4. Escalabilidade

| Camada | Risco | Mitigação |
|--------|-------|-----------|
| SQLite | Lock / tabela única grande | Índices em colunas de filtro (`uf`, `data`); Fase B incremental |
| Ingest | Janela de dias crescente | `--days` configurável; logs de duração |
| API | Endpoints sem paginação | `limit`/`offset` ou cursor onde a lista pode crescer |
| Classificador | Keywords estáticas | Documentar em `docs/NICHOS.md`; versão no código |
| Deploy | Monorepo | Manter front/back desacoplados via contrato REST |

**Pergunta-chave:** “O que quebra primeiro se PI virar multi-UF ou multi-nicho?”

### 5. Tratamento de erros

| Checar | Esperado |
|--------|----------|
| Externos | PNCP/HTTP: timeout, status 5xx, corpo inválido — log + mensagem acionável |
| CLI | Exit code ≠ 0 em falha; stderr legível |
| API | `HTTPException` com status correto; não vazar stack trace em produção |
| Frontend | Estados error/empty/loading; retry ou mensagem clara ao usuário |
| Dados | `None`/campo ausente no JSON PNCP — defaults seguros, não crash |
| Silêncio | Evitar `except: pass` — logar ou re-raise |

**Pergunta-chave:** “Se o PNCP cair às 7h, o operador sabe o que aconteceu?”

## Formato da auto-revisão (template)

```markdown
## Auto-revisão (5 ângulos)

| Ângulo | Status | Notas |
|--------|--------|-------|
| Performance | OK / Atenção / Corrigido | … |
| Legibilidade | … | … |
| Manutenibilidade | … | … |
| Escalabilidade | … | … |
| Tratamento de erros | … | … |

**Ações tomadas:** (se houve correção)
```

Status sugerido: **OK** (nada relevante), **Atenção** (dívida documentada ou aceitável no escopo), **Corrigido** (problema encontrado e resolvido neste PR).

## Severidade

| Nível | Ação |
|-------|------|
| Crítico | Corrigir antes de encerrar (bug, leak, perda de dados, falha silenciosa) |
| Médio | Corrigir se no escopo; senão registrar em Atenção |
| Baixo | Opcional; anotar para backlog |

## Exceções

- Hotfix urgente: revisão mínima (erros + regressão); completar os 5 ângulos depois.
- Docs-only: só Legibilidade aplicável.
