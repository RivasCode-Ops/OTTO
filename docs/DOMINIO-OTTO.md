# Domínio OTTO

## Visão

OTTO transforma publicações brutas do **PNCP** (Portal Nacional de Contratações Públicas) em **oportunidades priorizadas** para decisão comercial — não é apenas busca por palavra-chave.

## Fluxo

```
PNCP (API pública) → coleta → normalização → SQLite → classificação (nicho) → score → painel
```

## Entidades

| Entidade | Descrição |
|----------|-----------|
| **Oportunidade** | Edital/contratação normalizada, chave `numeroControlePncp` |
| **IngestRun** | Log de cada execução de coleta (UF, janela, totais) |
| **OportunidadeEvento** | Mudança detectada (situação, valor, prazo) |

Painel e colunas: [QUADRO-OTTO.md](./QUADRO-OTTO.md).

## Campos Otto (além do PNCP)

- `nicho` — ex.: `ti_software`, `outros`
- `confiancaClassificacao` — `alta` | `baixa`
- `scoreTotal` — 0–100
- `scoreDetalhe` — JSON com breakdown
- `qualidadeDados` — `ok` | `incompleto` | `suspeito`

## API PNCP (consulta pública)

- Base: `https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao`
- Parâmetros: `dataInicial`, `dataFinal` (YYYYMMDD), `uf`, `codigoModalidadeContratacao`, `pagina`, `tamanhoPagina`
- **Sem autenticação** para leitura ([Dados Abertos](https://www.gov.br/pncp/pt-br/acesso-a-informacao/dados-abertos))

## MVP

- UF: **PI** (Piauí) — padrão V1 produto; SP foi usado na validação técnica inicial
- Nicho: **TI/software** (regras por keyword)
- Persistência: **SQLite** (`data/otto.db`)
