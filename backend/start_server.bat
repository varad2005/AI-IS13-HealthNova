@echo off
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
echo.
echo ============================================================
echo Starting Rural Healthcare Platform Server
echo ============================================================
echo.
python app.py
pause
