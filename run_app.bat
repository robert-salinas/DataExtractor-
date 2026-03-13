@echo off
setlocal
title RS DataExtractor- Launcher
color 06

echo ============================================
echo      RS DIGITAL - DATAEXTRACTOR-
echo ============================================
echo.

:: 1. Verificar entorno virtual
if exist ".venv" goto :venv_exists
echo [INFO] Creando entorno virtual...
python -m venv .venv
:venv_exists


:: 2. Activar y asegurar dependencias
call .venv\Scripts\activate

:: Check if dependencies are already installed by looking for a marker file
if exist ".venv\.installed" goto :skip_install
echo [INFO] Instalando dependencias (solo la primera vez)...
pip install -r requirements.txt --quiet
python -m playwright install chromium
echo installed > .venv\.installed
:skip_install

:: 3. Iniciar GUI directamente
echo [INFO] Iniciando DataExtractor- Desktop...
python main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] La aplicacion se cerro con errores.
    pause
)

exit
