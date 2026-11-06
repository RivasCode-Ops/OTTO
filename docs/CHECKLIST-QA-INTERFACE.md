# Checklist QA — Interface OTTO (15 min)

Use após mudanças no painel React. Abra `http://127.0.0.1:5194` com API rodando.

---

## 0. Preparação (1 min)

- [ ] `INICIAR-OTTO.bat` ou API `:8791` + app `:5194` ativos
- [ ] Banco com dados PI (`otto ingest --days 7`) **ou** propositalmente vazio para testar empty states

---

## 1. Sidebar (2 min)

- [ ] Item **Radar** claramente ativo (fundo teal, contraste alto)
- [ ] Seções **Em breve** e **Configuração** visíveis como rótulos, não clicáveis
- [ ] Itens V2 desabilitados parecem “planejado”, não quebrado (opacidade, hint V2, tooltip “versão futura”)
- [ ] Hover só nos itens habilitados

---

## 2. TopBar (2 min)

- [ ] Pill `PI · TI/software` legível
- [ ] Busca filtra tabela e cards em tempo real
- [ ] Período 7/15/30 altera contagem
- [ ] **Atualizar** mostra estado loading no botão
- [ ] Toggle tema claro/escuro persiste após F5

---

## 3. KPIs (2 min)

- [ ] 6 cards alinhados, números tabulares, rótulos consistentes
- [ ] **Alta confiança** destacado (accent)
- [ ] **Vence 7d** em âmbar quando > 0
- [ ] **Mudanças recentes** reflete API (`/api/eventos/recentes`)
- [ ] Skeleton aparece no primeiro load (desligue API 2s para simular)

---

## 4. Prioridade + Mudanças (3 min)

- [ ] Cards top 5 clicáveis; seleção com borda teal
- [ ] Prazo urgente (≤7d) em âmbar
- [ ] Empty state quando filtro zera resultados (mensagem diferente de “banco vazio”)
- [ ] Bloco **Mudanças recentes**: empty elegante se 0 eventos
- [ ] Clique em evento abre drawer da oportunidade

---

## 5. Tabela (3 min)

- [ ] Score e valor **alinhados à direita**
- [ ] Zebra striping discreto
- [ ] Hover e linha selecionada distinguíveis
- [ ] Toggle “somente alta confiança” funciona
- [ ] Empty state com hint contextual (busca vs filtro vs sem ingest)

---

## 6. Drawer (2 min)

- [ ] Abre com animação lateral; backdrop escurece lista (contexto preservado)
- [ ] **×** e clique fora fecham
- [ ] Skeleton “Carregando detalhe…” ao trocar linha
- [ ] Score explicado **aprofunda** (barras + labels), não repete só a tabela
- [ ] Link PNCP funciona

---

## 7. Dark mode — contraste (2 min)

- [ ] Teal (ação/score alto) legível no escuro
- [ ] Âmbar (urgência) legível no escuro **e** no claro
- [ ] Texto secundário não “some” nos cards
- [ ] Bordas visíveis sem ser pesadas

---

## 8. Erro (opcional, 1 min)

- [ ] Pare API → banner vermelho + **Tentar novamente**
- [ ] Retry restaura painel sem F5

---

## 9. Alertas V1 (2 min)

- [ ] Banner **Radar ativo** aparece quando há novidades desde última visita
- [ ] **Marcar como visto** esconde banner e persiste após F5
- [ ] Clique em item do banner abre drawer
- [ ] `otto alertas --hours 24` no terminal lista o mesmo recorte
- [ ] (Opcional) Notificações browser após permissão

---

## Critério “passou”

| Área | Passou? |
|------|---------|
| Hierarquia clara (KPI → prioridade → tabela) | |
| Estados loading / empty / erro | |
| Drawer sem quebrar fluxo | |
| Dark mode usável 10+ min | |

**Veredicto:** ___ / 8 seções OK → pronto para uso diário interno.

---

## Comandos úteis

```bat
INICIAR-OTTO.bat
curl http://127.0.0.1:8791/api/eventos/recentes?uf=PI
```
