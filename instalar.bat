@echo off
setlocal
cd /d "%~dp0"

echo ============================================
echo   Instalador del Transcriptor Whisper
echo ============================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python no esta instalado o no esta en PATH.
    echo Instalalo desde https://www.python.org/downloads/ ^(marca "Add to PATH"^).
    pause
    exit /b 1
)

echo [1/4] Verificando ffmpeg...
where ffmpeg >nul 2>nul
if errorlevel 1 (
    echo       No encontrado. Instalando con winget...
    winget install -e --id Gyan.FFmpeg --accept-source-agreements --accept-package-agreements
    if errorlevel 1 (
        echo [ERROR] No se pudo instalar ffmpeg con winget.
        echo Instalalo manualmente desde https://www.gyan.dev/ffmpeg/builds/
        pause
        exit /b 1
    )
    echo       ffmpeg instalado. Tras la instalacion, puede ser necesario reiniciar la sesion.
) else (
    echo       OK.
)

echo.
echo [2/4] Creando entorno virtual...
if not exist .venv (
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] No se pudo crear el entorno virtual.
        pause
        exit /b 1
    )
) else (
    echo       Ya existe ^(.venv^).
)

echo.
echo [3/4] Actualizando pip...
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip

echo.
echo [4/4] Instalando dependencias ^(esto puede tardar^)...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Fallo la instalacion de dependencias.
    pause
    exit /b 1
)

echo.
echo ============================================
echo   Instalacion completada
echo ============================================
echo Ejecuta Transcriptor.bat para abrir la app.
echo.
pause
