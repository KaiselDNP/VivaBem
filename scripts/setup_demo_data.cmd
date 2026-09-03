@echo off
setlocal
cd /d "%~dp0.."

if not exist ".venv\Scripts\python.exe" (
    echo Ambiente virtual nao encontrado. Crie a pasta .venv e instale requirements/dev.txt.
    exit /b 1
)

call ".venv\Scripts\python.exe" manage.py migrate --noinput
if errorlevel 1 exit /b 1

call ".venv\Scripts\python.exe" manage.py seed_demo_data
if errorlevel 1 exit /b 1

echo Dados ficticios preparados com sucesso.
