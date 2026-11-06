# DOCX (autorizado 2026-11-06)

Arquivos **Word .docx** são aceitos no upload local. Extração com `python-docx` neste computador — sem nuvem.

## Comportamento

- Lê **parágrafos** e células de **tabelas**.
- Guarda o texto como **uma página lógica (1)** — não há paginação física confiável no DOCX sem renderizar.
- Na evidência (ficha/requisitos), **página é opcional** (igual TXT).
- Imagens dentro do DOCX **não** passam por OCR nesta fatia (só texto embutido).

## Não suportado

- `.doc` (Word 97–2003)

Download seletivo do PNCP (inclui DOCX quando o anexo for `.docx`): [DOWNLOAD-ANEXOS.md](DOWNLOAD-ANEXOS.md).

## Dependência

Já listada no `otto-core` (`python-docx`). Após pull: `INSTALAR-OTTO.bat` ou `pip install -e packages/otto-core…`.
