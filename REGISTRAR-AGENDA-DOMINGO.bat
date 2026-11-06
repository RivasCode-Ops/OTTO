@echo off
setlocal
cd /d "%~dp0"

set TASK_NAME=OTTO Reconciliacao PI Domingo
set BAT=%~dp0AGENDAR-INGEST-SEMANAL.bat

echo Registrando tarefa semanal: %TASK_NAME%
echo Script: %BAT%
echo Horario: domingo as 06:00
echo Janela: 14 dias (reconciliacao Fase A)
echo.

schtasks /Create /F /TN "%TASK_NAME%" /TR "\"%BAT%\"" /SC WEEKLY /D SUN /ST 06:00
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
echo Log semanal: %~dp0logs\agendado-semanal.log
echo Remover: schtasks /Delete /F /TN "%TASK_NAME%"
pause
