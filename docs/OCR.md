# OCR local (autorizado 2026-11-06)

PDF **sem texto selecionável** (digitalizado) é lido neste computador com **Tesseract**. Sem nuvem.

## O que o OTTO faz

1. Tenta extrair texto nativo do PDF (`pypdf`).
2. Se não houver texto (ou páginas vazias), usa OCR local (`pypdfium2` + Tesseract).
3. Status possível: `ok` (com aviso de OCR), `ocr_necessario` (motor ausente), `sem_texto`, `falhou`.
4. Documentos antigos em `ocr_necessario`: botão **Reprocessar OCR** no detalhe da oportunidade (ou `POST .../documentos/{id}/ocr`).

## Instalar o motor (Windows)

1. Instale [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) (instalador UB Mannheim).
2. Marque o idioma **Portuguese** (`por`).
3. Confirme o executável, em geral:  
   `C:\Program Files\Tesseract-OCR\tesseract.exe`
4. Opcional: variável `OTTO_TESSERACT_CMD` apontando para o `.exe`.
5. Pacotes Python (já no `otto-core`): `pypdfium2`, `pytesseract`, `Pillow` — rode de novo `INSTALAR-OTTO.bat` ou:

```bat
.\.venv\Scripts\activate.bat
pip install -e "packages/otto-core[dev]" -e services/ingest -e api
```

6. Reinicie `INICIAR-OTTO.bat`. Em **Configurações**, OCR deve aparecer como *motor local disponível*.

## Limites

- Lento em CPU fraca (i3) e em PDF com muitas páginas.
- Qualidade depende do scan; revise trechos antes de aplicar sugestões de IA.
- DOCX: ver [DOCX.md](DOCX.md) (texto; sem OCR de imagens dentro do Word). Download PNCP: [DOWNLOAD-ANEXOS.md](DOWNLOAD-ANEXOS.md).
