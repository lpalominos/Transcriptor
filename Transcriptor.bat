@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\pythonw.exe" (
    echo Entorno virtual no encontrado. Ejecuta instalar.bat primero.
    pause
    exit /b 1
)
start "" ".venv\Scripts\pythonw.exe" "%~dp0transcriptor_gui.py"
