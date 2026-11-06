@echo off
setlocal
cd /d "%~dp0"
title OTTO

if not exist ".venv" (
  echo Rode INSTALAR-OTTO.bat primeiro.
  pause
  exit /b 1
)

echo.
echo OTTO - Painel http://127.0.0.1:5194  API http://127.0.0.1:8791
echo.

call .venv\Scripts\activate.bat
start "OTTO-API" cmd /k "cd /d %~dp0 && call .venv\Scripts\activate.bat && uvicorn otto_api.main:app --host 127.0.0.1 --port 8791 --reload --app-dir api/src"
timeout /t 2 /nobreak >nul
npm run dev --prefix app
