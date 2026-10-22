@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo       MUNDO LIBRO - INTERFAZ WEB
echo ============================================
echo.
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 web_app.py
) else (
  python web_app.py
)
if errorlevel 1 (
  echo.
  echo El sistema no pudo iniciar. Lee el mensaje anterior.
  pause
)
endlocal
