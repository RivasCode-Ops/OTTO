# 4. Security Review (Blindagem)

Revisão de segurança obrigatória ao **finalizar** código que toca dados, rede, persistência ou UI — e **durante** a implementação em superfícies de ataque.

## Quando aplicar

- Novos endpoints, queries, formulários ou integrações externas.
- Alteração em CORS, auth, paths de arquivo ou config.
- Antes de expor API/painel além de `localhost` (V1 local).

## Checklist principal

### SQL Injection

| Fazer | Evitar |
|-------|--------|
| Placeholders `?` / parâmetros nomeados em **todos** os valores user-controlled | Concatenar input em SQL: `f"SELECT … WHERE uf = '{uf}'"` |
| Whitelist para enums (`uf`, `nicho`, `order_by`) | Interpolar nomes de coluna/tabela vindos do cliente |
| Funções centralizadas em `otto_core/db.py` | SQL ad hoc espalhado com strings dinâmicas |

Padrão OTTO (correto):

```python
q += " AND uf = ?"
params.append(uf)
conn.execute(q, params)
```

Se `WHERE` dinâmico usar `f"… {where}"`, garantir que `where` é montado só com fragmentos fixos + `params`.

### XSS (Cross-Site Scripting)

| Fazer | Evitar |
|-------|--------|
| React: renderizar texto com `{valor}` (escape automático) | `dangerouslySetInnerHTML` com dados PNCP/API |
| URLs externas: `href` com `rel="noopener noreferrer"` em nova aba | `javascript:` ou URLs não validadas |
| Tratar campos PNCP (`objeto_compra`, etc.) como **texto**, não HTML | `innerHTML` / `document.write` |

Dados do PNCP são não confiáveis — nunca interpretar como markup.

### CSRF

| Contexto OTTO V1 | Ação futura |
|------------------|-------------|
| API read-only GET, sem cookies de sessão, CORS restrito a dev | Ao adicionar POST/PUT/DELETE ou auth por cookie: token CSRF ou SameSite + origin check |
| CORS: manter lista explícita de `allow_origins` | `allow_origins=["*"]` com credenciais |

Arquivo de referência: `api/src/otto_api/main.py` — não alargar CORS sem necessidade.

### Secrets e configuração

| Fazer | Evitar |
|-------|--------|
| Variáveis de ambiente (`OTTO_DATA_DIR`, `OTTO_DB_PATH`, futuras API keys) | Chaves/tokens no código, commit ou logs |
| Documentar novas vars em `.env.example` | `.env` real no git |
| `config.py` / startup lendo `os.environ` | Imprimir secrets em stderr ou respostas HTTP |

PNCP público hoje não exige chave; se integrar serviço autenticado, usar env + `.gitignore`.

### Validação de inputs

| Camada | Regra |
|--------|-------|
| API (FastAPI) | `Query(..., ge=, le=, pattern=)`; enums whitelist (`uf` 2 letras, `nicho` conhecidos) |
| Path params | Validar formato (`numero_controle_pncp`); 404 genérico, sem stack trace |
| CLI | Tipos argparse; rejeitar paths absurdos |
| Frontend | Validar antes de enviar; não confiar só no client |
| Ingest | Validar/normalizar JSON PNCP antes de persistir |

Princípio: **nunca confiar** em query string, body, headers ou arquivo externo sem validação.

## Superfícies OTTO

| Superfície | Riscos |
|------------|--------|
| `otto_core/db.py` | SQL injection, path traversal via DB path |
| `otto_api/main.py` | Input abuse, info leak, CORS |
| `app/` (React) | XSS, open redirect em links PNCP |
| `otto_ingest` / PNCP client | SSRF se URL configurável; DoS por timeout ausente |
| Scripts `scripts/` | Apenas dev local — não expor como serviço |

## Formato da revisão (template)

```markdown
## Security Review (Blindagem)

| Item | Status | Notas |
|------|--------|-------|
| SQL Injection | OK / Risco / Corrigido | … |
| XSS | … | … |
| CSRF | N/A / OK / Risco | … |
| Secrets / env | … | … |
| Validação de inputs | … | … |

**Ações tomadas:** …
```

## Severidade

| Nível | Exemplos | Ação |
|-------|----------|------|
| Crítico | SQLi, secret no repo, XSS stored, SSRF aberto | Bloquear merge até corrigir |
| Alto | Input sem validação em endpoint público | Corrigir no escopo |
| Médio | CORS largo demais, logs verbosos com PII | Corrigir ou documentar + issue |
| Baixo | Hardening opcional (headers de segurança) | Backlog |

## Exceções

- Scripts locais one-off: revisão mínima (sem SQL concat, sem secrets).
- Docs-only: N/A salvo menção a credenciais reais (proibido).

## Referências no repo

- `.env.example` — vars permitidas
- `.gitignore` — `data/`, `.env`, logs
- Regra #3 — incluir “Tratamento de erros” junto com blindagem ao finalizar
