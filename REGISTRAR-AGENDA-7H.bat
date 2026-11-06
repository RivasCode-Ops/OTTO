@echo off
setlocal
cd /d "%~dp0"

set TASK_NAME=OTTO Ingest PI 7h
set BAT=%~dp0AGENDAR-INGEST.bat

echo Registrando tarefa diaria: %TASK_NAME%
echo Script: %BAT%
echo Horario: todo dia as 07:00
echo Janela: 2 dias (Fase A incremental)
echo.

schtasks /Create /F /TN "%TASK_NAME%" /TR "\"%BAT%\"" /SC DAILY /ST 07:00
if errorlevel 1 (
  echo.
  echo Falhou. Tente como Administrador ou use docs/AGENDADOR-WINDOWS.md
  pause
  exit /b 1
)

echo.
echo Tarefa criada. Teste:
echo   schtasks /Run /TN "%TASK_NAME%"
echo.
echo Log diario: %~dp0logs\agendado.log
echo Reconciliacao semanal: REGISTRAR-AGENDA-DOMINGO.bat
pause
