# Instalação e uso local — LICITAR (base OTTO)

**Atualizado:** 2026-11-06  
**Objetivo:** um único caminho para instalar, abrir, coletar e encerrar neste computador.

O código vive no repositório **OTTO**; o produto em evolução chama-se **LICITAR** (`README.txt` = especificação). Este guia cobre o **app operacional** (API + painel React), não o painel de acompanhamento em `docs/licitar-acompanhamento/`.

---

## Requisitos

| Ferramenta | Versão |
|------------|--------|
| Windows | 10+ |
| Python | 3.11+ (`python` no PATH) |
| Node.js | 18+ (`node` / `npm` no PATH) |

Opcional (análise documental por IA local): Ollama + modelo — ver [IA-LOCAL.md](IA-LOCAL.md). Sem isso, o restante do app funciona.

---

## Instalar (uma vez)

Na pasta do projeto (`D:\PROJETOS\04_LABS\OTTO` ou clone equivalente):

```bat
INSTALAR-OTTO.bat
```

O script:

1. Cria `.venv` se não existir  
2. Instala `otto-core`, `otto-ingest`, `otto-api` em modo editável  
3. Roda `npm install` em `app/` se ainda não houver `node_modules`  
4. Garante a pasta `data/`

**Manual (PowerShell), se preferir:**

```powershell
cd D:\PROJETOS\04_LABS\OTTO
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e "packages/otto-core[dev]" -e services/ingest -e api
npm install --prefix app
mkdir data -Force
```

---

## Abrir o aplicativo

```bat
INICIAR-OTTO.bat
```

| Peça | URL |
|------|-----|
| **App (use este)** | http://127.0.0.1:5194 |
| API (health) | http://127.0.0.1:8791/health |

- O Vite escuta em **127.0.0.1** (IPv4). Não use só `localhost` se no seu Windows isso for IPv6 e a página não abrir.  
- A API fica em janela `OTTO-API`; o painel fica no terminal do `INICIAR-OTTO.bat`.

### Encerrar

1. Feche a janela **OTTO-API** (ou Ctrl+C nela)  
2. Ctrl+C no terminal do Vite / `INICIAR-OTTO.bat`

---

## Primeira coleta PNCP

Com o venv ativo (ou após `INSTALAR-OTTO.bat`):

```bat
.\.venv\Scripts\activate.bat
otto ingest --days 7
```

Ou pela UI: **Configurações → Coleta PNCP → Atualizar coleta agora** (janela 2 / 7 / 14 dias). Só uma coleta por vez.

UF e modalidade padrão: `config/ingest.yaml` (V1: PI, pregão eletrônico).

Agendamento Windows (opcional): [AGENDADOR-WINDOWS.md](AGENDADOR-WINDOWS.md).

---

## Onde estão os dados

| Caminho | Conteúdo |
|---------|----------|
| `data/otto.db` | SQLite (oportunidades, fluxo, IA, auditoria) |
| `data/documentos/` | Anexos locais por oportunidade |
| `data/backups/` | Zips de backup (Configurações) |
| `data/ia-models/` | Pesos sugeridos do Ollama (se usar IA local) |

**Não** commitar `.env`, `data/*.db`, `logs/`, `node_modules/`.

Backup pela UI: Configurações → Criar backup. Restauração **operacional** (substituir `otto.db`) não está na UI — procedimento restrito.

---

## Dois “painéis” (não confundir)

| O quê | Como abrir | Para quê |
|-------|------------|----------|
| **App LICITAR/OTTO** | `INICIAR-OTTO.bat` → http://127.0.0.1:5194 | Oportunidades, documentos, IA, config |
| **Acompanhamento de construção** | Duplo clique em `docs/licitar-acompanhamento/painel.html` | Status de desenvolvimento; **não** é o produto |

---

## Verificação rápida

1. `curl http://127.0.0.1:8791/health` → `{"ok":true,...}`  
2. Abrir http://127.0.0.1:5194 → lista / banner de cobertura  
3. (Opcional) `pytest packages/otto-core/tests/` e `npm run typecheck --prefix app`

Detalhes de stack: [TECH_STACK.md](../TECH_STACK.md) · arquitetura: [ARCHITECTURE.md](../ARCHITECTURE.md).

---

## Problemas comuns

| Sintoma | O que fazer |
|---------|-------------|
| `127.0.0.1:5194` recusa conexão | Rode `INICIAR-OTTO.bat`; confira se o Vite imprimiu `http://127.0.0.1:5194/` |
| API sobe, app não | Só a API estava ligada — falta o `npm run dev` (o bat sobe os dois) |
| `Python nao encontrado` | Instale 3.11+ e marque “Add to PATH” |
| `otto` não é comando | Ative `.venv` ou use `.\.venv\Scripts\otto.exe` |
| Coleta lenta / vazia | Rede + janela de dias; veja Configurações → última execução |
| IA local indisponível | [IA-LOCAL.md](IA-LOCAL.md) |
| PDF só-imagem / `ocr_necessario` | Instale Tesseract (`por`) — [OCR.md](OCR.md); depois **Reprocessar OCR** no documento |
| Anexos do PNCP na oportunidade | Documentos → **Buscar anexos no PNCP** → baixar PDF/DOCX/TXT — [DOWNLOAD-ANEXOS.md](DOWNLOAD-ANEXOS.md) |

---

## Fora desta instalação (aguardam autorização)

Restauração operacional do banco pela UI · especializações Saúde/Viagens · priorização avançada de órgãos.
