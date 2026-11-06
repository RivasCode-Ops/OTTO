# Download de anexos PNCP (autorizado 2026-11-06)

Baixa **sob demanda** os arquivos listados pela API pública do PNCP para `data/documentos/`, na oportunidade aberta.

## Como usar

1. Abra uma oportunidade **vinda da coleta PNCP** (com `raw_json` contendo CNPJ/ano/sequencial).
2. Documentos → **Buscar anexos no PNCP**.
3. **Baixar PDF/DOCX/TXT listados** (até 10 por disparo; já locais são pulados).

Cadastro **manual** sem metadados PNCP: a listagem informa que não há IDs de compra.

## Regras de segurança

| Regra | Valor |
|-------|--------|
| Hosts | só `pncp.gov.br` / `www.pncp.gov.br` (HTTPS) |
| Redirect | máximo 3; destino final também na whitelist |
| Formatos gravados | PDF, DOCX, TXT (os mesmos do upload) |
| ZIP / outros | aparecem na lista, **não** baixados automaticamente |
| Tamanho | ≤ 25 MB |
| Origem no banco | `download_pncp` |

Sem chave de API. Sem envio a nuvem de terceiros.

## API

- `GET /api/oportunidades/{numero}/anexos-remotos`
- `POST /api/oportunidades/{numero}/anexos-remotos/baixar`  
  body opcional: `{ "sequenciais": [1,2], "max_arquivos": 10 }`

## Limites

- Endpoint PNCP: `/api/pncp/v1/orgaos/{cnpj}/compras/{ano}/{sequencial}/arquivos`
- Edital em ZIP continua manual (extraia e anexe o PDF/DOCX).
- Após o download, vale a mesma extração/OCR/IA dos uploads locais.
