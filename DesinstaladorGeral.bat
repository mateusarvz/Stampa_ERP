@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0DesinstaladorGeral.ps1" -Silent
exit /b %errorlevel%
