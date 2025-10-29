@echo off
REM ETL Movilidad Medellin - Scheduler
REM Ejecuta el pipeline cada 20 minutos automaticamente

echo ============================================================
echo ETL MOVILIDAD MEDELLIN - SCHEDULER
echo ============================================================
echo.
echo Este script ejecutara el pipeline cada 20 minutos
echo Presiona Ctrl+C para detener
echo.
echo ============================================================
echo.

REM Activar el entorno virtual si existe
if exist venv\Scripts\activate.bat (
    echo Activando entorno virtual...
    call venv\Scripts\activate.bat
)

REM Ejecutar el scheduler
python scheduler_advanced.py

pause
