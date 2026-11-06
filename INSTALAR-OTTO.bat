@echo off
setlocal
cd /d "%~dp0"
title OTTO - instalacao

where python >nul 2>&1
if errorlevel 1 (
  echo ERRO: Python 3.11+ nao encontrado. Instale em https://python.org
  pause
  exit /b 1
)

where node >nul 2>&1
if errorlevel 1 (
  echo ERRO: Node.js 18+ nao encontrado. Instale em https://nodejs.org
  pause
  exit /b 1
)

echo.
echo OTTO / LICITAR - Instalacao
python --version
node -v
echo.

if not exist ".venv" (
  echo [1/3] Criando venv...
  python -m venv .venv
  if errorlevel 1 goto :fail
)

call .venv\Scripts\activate.bat

echo [2/3] Python ^(otto-core, ingest, api^)...
pip install -q -e "packages/otto-core[dev]" -e services/ingest -e api
if errorlevel 1 goto :fail

echo [3/3] App React...
if not exist "app\node_modules" (
  call npm install --prefix app
  if errorlevel 1 goto :fail
)

if not exist "data" mkdir data

echo.
echo OK.
echo   Guia: docs\INSTALACAO.md
echo   Abrir: INICIAR-OTTO.bat  -^>  http://127.0.0.1:5194
echo   Coleta: otto ingest --days 7  ^(ou Configuracoes no app^)
echo.
pause
exit /b 0

:fail
echo.
echo FALHA na instalacao. Veja a mensagem acima e docs\INSTALACAO.md
pause
exit /b 1
