# Como abrir o painel de acompanhamento do LICITAR

Este painel **não é** o aplicativo de oportunidades.  
Ele só mostra o andamento da construção do LICITAR.

**Não atualiza sozinho** (não é tempo real). Se a conversa com o assistente estiver parada, o trabalho também está parado.

## Abrir (sem programar)

1. No Explorador de Arquivos, vá até a pasta do projeto OTTO.
2. Abra: `docs` → `licitar-acompanhamento`
3. Dê dois cliques em **`painel.html`**
4. O navegador deve mostrar o resumo com data/hora no topo.

Caminho completo típico:

`D:\PROJETOS\04_LABS\OTTO\docs\licitar-acompanhamento\painel.html`

## Se a página aparecer vazia ou com erro de dados

Alguém com acesso ao projeto deve, na pasta do painel, rodar:

`python sync-dados.py`

Depois, abra de novo o `painel.html`.

## Arquivos desta pasta

| Arquivo | Para quem |
|---------|-----------|
| `painel.html` | Você — acompanhar o projeto |
| `dados.json` | Fonte única dos textos do painel |
| `dados.js` | Cópia automática usada pelo navegador |
| `README.md` | Estas instruções |
| `diagnostico.md` / `plano-continuidade.md` | Notas técnicas adicionais |

O aplicativo LICITAR fica em outro lugar: normalmente http://127.0.0.1:5194 depois de rodar `INICIAR-OTTO.bat` (nome interno do script).
