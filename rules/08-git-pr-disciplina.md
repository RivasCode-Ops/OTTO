# 8. Git / PR (Disciplina de entrega)

Regra para **versionamento, commits e pull requests** — escopo mínimo, nada de segredos no diff, entrega só quando o humano pedir.

Complementa #6 (QA sign-off antes de considerar pronto) e #4 (nada de `.env`/secrets no commit).

## Quando aplicar

- Antes de `git add`, `commit`, `push` ou `gh pr create`.
- Ao preparar entrega após QA (#6) aprovado.
- Quando o usuário pedir commit ou PR explicitamente.

---

## 1. O que NUNCA fazer (sem pedido explícito)

| Proibido | Motivo |
|----------|--------|
| `git commit` | Só commitar quando o usuário pedir |
| `git push` | Idem |
| `git push --force` em `main`/`master` | Destrutivo — avisar se pedido |
| `git config` (alterar) | Config é do operador |
| `--no-verify` / pular hooks | Só se o usuário pedir |
| `git commit --amend` | Só se todas as condições de segurança forem atendidas (commit seu, não pushed, usuário pediu ou hook auto-modificou) |
| Commitar `.env`, `data/*.db`, `logs/` | `.gitignore` — dados locais e secrets |

---

## 2. Escopo do diff

| Princípio | Aplicação OTTO |
|-----------|----------------|
| **Uma intenção por commit/PR** | Ex.: “classificador v2.1” ≠ “refactor painel + ingest” |
| **Diff mínimo** | Só arquivos do plano (#1); sem “aproveitei e arrumei” |
| **Sem scope creep** | Melhorias laterais → issue ou commit separado |
| **Docs alinhados** | Mudou stack/arquitetura → `TECH_STACK.md` / `ARCHITECTURE.md` / `docs/` no mesmo ciclo |

---

## 3. Antes de commitar (checklist)

Rodar **somente leitura** primeiro:

```powershell
git status
git diff
git log -3 --oneline
```

### Gate obrigatório

| Verificação | Comando |
|-------------|---------|
| Testes core | `pytest packages/otto-core/tests/` |
| Typecheck (se `app/` tocado) | `npm run typecheck --prefix app` |
| Sem secrets | diff não contém `.env`, tokens, paths com credenciais |
| Sem dados locais | diff não contém `data/*.db`, `logs/` |

### Gate por tipo de mudança

| Mudança | Extra |
|---------|-------|
| Painel | `docs/CHECKLIST-QA-INTERFACE.md` (amostra) |
| Ingest / PI | `python scripts/validate-pi.py` |
| Classificador | `python scripts/ti-summary.py` |
| Regra nova | `rules/` + `.cursor/rules/` pareados |

Revisões #3 (code review) e #4 (security) já feitas ou registradas.

---

## 4. Mensagem de commit

- **1–2 frases**, foco no **porquê**, não lista de arquivos.
- Estilo imperativo: `Adiciona…`, `Corrige…`, `Atualiza…`.
- Português ou inglês — **consistente com os últimos commits** do repo (`git log`).

Exemplos OTTO:

```text
Adiciona regra #7 de backend e docs TECH_STACK/ARCHITECTURE.

Corrige classificador TI v2.1 para hospedagem contextual.
```

Passar mensagem via HEREDOC no shell (evita quebra de aspas no Windows/PowerShell — adaptar conforme shell).

---

## 5. Pull request

Só criar PR quando o usuário pedir. Usar `gh`:

1. `git status` + `git diff` + histórico desde a base.
2. Push com `-u` se necessário.
3. `gh pr create` com corpo:

```markdown
## Summary
- …

## Test plan
- [ ] pytest
- [ ] typecheck (se app)
- [ ] …
```

Incluir **URL do PR** na resposta ao usuário.

---

## 6. Arquivos sensíveis (OTTO)

Confirmar que **não entram** no stage:

| Path | Motivo |
|------|--------|
| `.env`, `.env.local` | Secrets |
| `data/*.db`, `data/raw/` | Dados locais |
| `logs/` | Logs operacionais |
| `.venv/`, `node_modules/` | Dependências |
| `__pycache__/` | Artefatos |

Se o usuário pedir commit incluindo algo sensível → **avisar** antes de prosseguir.

---

## 7. Fluxo completo de entrega

```text
#6 QA ✅ → usuário pede commit
  → checklist #8 → git add (relevante) → commit → (se pedido) push → (se pedido) PR
```

---

## 8. Template sign-off Git

```markdown
## Git — pronto para commit

**Pedido explícito do usuário:** sim / não

| Item | OK |
|------|-----|
| Escopo único | |
| pytest | |
| typecheck (se app) | |
| Sem secrets/dados locais no stage | |
| Mensagem de commit draft | … |

**Ação:** aguardando OK / commit feito / PR: URL
```

---

## Exceções

- Usuário pediu só `git status` ou `git diff`: informar, não commitar.
- WIP local: branch ou stash — não commitar lixo intermediário sem combinar.

## Referências

- [rules/06-stack-gerente-engenharia.md](./06-stack-gerente-engenharia.md) — QA antes de concluir
- [rules/04-security-review-blindagem.md](./04-security-review-blindagem.md) — secrets
- `.gitignore` na raiz do OTTO
