# OTTO — Agendador de Tarefas (Windows)

Rotina **Fase A incremental**:

| Tarefa | Script | Janela |
|--------|--------|--------|
| Diária **7h** | `AGENDAR-INGEST.bat` | 2 dias + alertas 24h |
| Domingo **6h** | `AGENDAR-INGEST-SEMANAL.bat` | 14 dias (reconciliação) |

Logs: `logs\agendado.log` · `logs\agendado-semanal.log`

---

## Opção A — Um clique (recomendado)

1. Confirme que `INSTALAR-OTTO.bat` já rodou (existe `.venv`).
2. **`REGISTRAR-AGENDA-7H.bat`** — ingest diária (2 dias) às 7h.
3. **`REGISTRAR-AGENDA-DOMINGO.bat`** — reconciliação semanal (14 dias) domingo 6h.
4. Teste manual:
   ```bat
   schtasks /Run /TN "OTTO Ingest PI 7h"
   schtasks /Run /TN "OTTO Reconciliacao PI Domingo"
   ```
5. Logs: `logs\agendado.log` e `logs\agendado-semanal.log`.

---

## Opção B — Interface gráfica (passo a passo)

### 1. Abrir o Agendador

- Tecla **Win + R** → digite `taskschd.msc` → Enter  
- Ou: **Painel de Controle** → Ferramentas administrativas → **Agendador de Tarefas**

### 2. Criar tarefa básica

1. Painel direito → **Criar Tarefa Básica…**
2. Nome: `OTTO Ingest PI 7h`
3. Descrição: `Coleta PNCP PI + alertas OTTO`
4. **Avançar**

### 3. Disparo diário

1. **Diariamente** → Avançar
2. Hora: **07:00:00**
3. Recorrência: **1** dia → Avançar

### 4. Ação

1. **Iniciar um programa** → Avançar
2. Preencha:

| Campo | Valor |
|-------|--------|
| **Programa/script** | `D:\PROJETOS\OTTO\AGENDAR-INGEST.bat` |
| **Iniciar em (opcional)** | `D:\PROJETOS\OTTO` |

> **Iniciar em:** use caminho **sem aspas** e **sem barra final** (`D:\PROJETOS\OTTO`, não `"D:\PROJETOS\OTTO\"`). Aspas ou `\` no fim podem gerar “diretório inválido” no Agendador.

> Ajuste o caminho se o repo estiver em outra pasta. **Iniciar em** evita erro de `.venv` não encontrado.

3. Avançar → **Concluir**

### 5. Testar antes de confiar

1. No Agendador, encontre **OTTO Ingest PI 7h**
2. Clique direito → **Executar**
3. Status deve ir para **Em execução** e depois **Pronto**
4. Confira `D:\PROJETOS\OTTO\logs\agendado.log`

### 6. Ajustes opcionais (Propriedades)

Clique direito na tarefa → **Propriedades**:

| Aba | Sugestão |
|-----|----------|
| **Geral** | Marque *Executar estando o usuário conectado ou não* se o PC ligar sem login (pede senha Windows) |
| **Condições** | Desmarque *Iniciar apenas se o computador estiver em energia CA* (notebook) |
| **Configurações** | *Se a tarefa falhar, reiniciar a cada* 10 minutos, até 3 tentativas |

---

## Validar rotina V1 (checklist 5 min)

Após **Executar** manual ou esperar 7h:

- [ ] `logs\agendado.log` com timestamp de hoje
- [ ] Linha `Coleta concluída: N bruto | …`
- [ ] Linha `Alertas OTTO · PI`
- [ ] Abrir painel → KPIs atualizados
- [ ] Banner de alertas se houver novidades desde última visita

---

## Comandos úteis

```bat
REM Executar agora
schtasks /Run /TN "OTTO Ingest PI 7h"

REM Ver próxima execução
schtasks /Query /TN "OTTO Ingest PI 7h" /V /FO LIST

REM Remover tarefa
schtasks /Delete /F /TN "OTTO Ingest PI 7h"

REM Rodar manual (sem agendador)
AGENDAR-INGEST.bat
```

---

## Problemas comuns

| Sintoma | Causa provável | Correção |
|---------|----------------|----------|
| Tarefa **Pronto (0x1)** | `.venv` ausente | Rodar `INSTALAR-OTTO.bat` |
| **Diretório inválido** | Aspas ou `\` no **Iniciar em** | `D:\PROJETOS\OTTO` sem aspas e sem barra final |
| Log vazio | Caminho errado no agendador | Conferir **Iniciar em** = pasta OTTO |
| Ingest 0 itens | Sem rede às 7h | Verificar internet; retry nas Propriedades |
| Painel não atualiza | API/painel não estão abertos | Normal — banco SQLite atualiza; abra `INICIAR-OTTO.bat` depois |

---

## Depois do agendamento

Com rotina diária estável, próxima frente técnica: **ingest incremental** (`dataAtualizacaoGlobal`) — menos carga no PNCP e coletas mais rápidas.

Ver: [ALERTAS-V1.md](./ALERTAS-V1.md) · [CHECKLIST-VALIDACAO-PI.md](./CHECKLIST-VALIDACAO-PI.md)
