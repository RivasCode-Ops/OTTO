# Checklist de Fase A – Operação

> **Nota:** Para problemas recorrentes ou casos específicos encontrados na operação, consulte a seção "Anotações de campo – casos reais" ao final deste documento.

## 1. Logs e `ingest_runs`

- Verificar em cada ciclo:
  - se o status de ingestão diária (2 dias) e semanal (14 dias) está como “OK”;  
  - se há mensagens repetidas de erro ou `database is locked`;  
  - se o tempo de execução foge muito do padrão (por exemplo, ingest normalmente leva 30 s e de repente passa a levar 5 min).
- Conferir, nos domingos, se a ingest de 14 dias:
  - encontra registros que **não** apareceram na janela curta;  
  - corrige alguma divergência de status.

> Se isso acontecer com frequência, vira insumo para a Fase B (uso de `dataAtualizacaoGlobal` e afins).

## 2. Painel e CLI no dia a dia

- No painel:
  - bater os **KPIs** com o esperado (quantidade de novas, mudanças, urgentes) em relação ao PNCP;  
  - conferir se o **drawer** de detalhe sempre traz dados coerentes (objeto, órgão, datas, valor, score).
- No CLI:
  - rodar ingest manualmente de vez em quando para ver se o comportamento coincide com o agendado;  
  - observar mensagens e tempos diretamente, sem a camada do agendador.

> Qualquer divergência entre painel, CLI e PNCP é sinal de que precisa investigar a normalização ou o score.

## 3. Ajustes a priorizar se surgirem sintomas

- **`get_alertas()`**
  - Se usuários interpretarem `total` como “número de alertas” e isso causar confusão, renomear ou ajustar o cálculo para refletir contagem real.
- **SQLite**
  - Se surgirem erros de `database is locked`, adicionar `timeout` maior e retry simples na conexão/escrita.
- **Datas / timezone**
  - Se aparecer inconsistência de prazo ou de ordenação no painel, revisar o tratamento para garantir que tudo está em UTC coerente.

> Enquanto nada disso aparece, não precisa gastar energia em micro-ajuste.

## 4. Coisas para deixar explicitamente para a Fase B

- Refino de `get_alertas()` e KPIs mais ricos (por exemplo, breakdown por categoria, tendência) baseado em operação real.
- Uso mais agressivo de `dataAtualizacaoGlobal` e janelas incrementais mais inteligentes.
- Qualquer mudança de infraestrutura (por exemplo, sair de SQLite) só depois de ter dados de uso e limite real atingido.
- Melhorias de caching de configs (`ingest.yaml`, `score.yaml`) se, na prática, a latência da V1 se mostrar problema.

> Fase A = **operar, observar, registrar sintomas**; Fase B = **corrigir o que doeu e elevar o nível**.

---

## Anotações de campo – casos reais

Use este espaço para registrar situações reais encontradas na operação da Fase A. Quando esta seção começar a crescer, pode ser reorganizada como um mini-guia formal de troubleshooting.

### Formato para cada entrada

- **Problema detectado:** [descrição breve]  
- **Como foi visto:** [sintoma observado no painel, logs, banco etc.]  
- **O que resolveu:** [ação tomada]  
- **Data:** [quando ocorreu]  

---

### Entradas (adicionar conforme surgirem)

*(Nenhuma entrada registrada ainda.)*
