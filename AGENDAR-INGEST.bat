@echo off
setlocal
cd /d "%~dp0"

REM Fase A incremental: janela curta diaria (default 2 dias)
set DIAS=2
if not "%~1"=="" set DIAS=%~1

if not exist "logs" mkdir logs
set LOG=logs\agendado.log

if not exist ".venv" (
  echo [%date% %time%] ERRO: .venv ausente >> "%LOG%"
  echo Rode INSTALAR-OTTO.bat primeiro.
  exit /b 1
)

call .venv\Scripts\activate.bat

(
  echo.
  echo ===== %date% %time% =====
  echo OTTO ingest diario — janela %DIAS% dia(s) + alertas
) >> "%LOG%"

otto ingest --days %DIAS% >> "%LOG%" 2>&1
if errorlevel 1 (
  echo [%date% %time%] ERRO ingest >> "%LOG%"
  exit /b 1
)

otto alertas --hours 24 >> "%LOG%" 2>&1
echo [%date% %time%] OK >> "%LOG%"
exit /b 0
