@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

REM Mata processo anterior se tiver rodando
echo Fechando versao anterior se tiver aberta...
taskkill /f /im StampaSaaS.exe 2>nul
timeout /t 1 /nobreak >nul

REM Detecta Python instalado ou usa venv
set PYTHON_EXE=python.exe
if exist ".venv_stampa\Scripts\python.exe" (
    set PYTHON_EXE=.venv_stampa\Scripts\python.exe
)

REM Verifica se Python existe
"%PYTHON_EXE%" --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo.
    echo ========================================
    echo ERRO: Python nao encontrado!
    echo Instale Python 3.9+ em: https://python.org
    echo ========================================
    pause
    exit /b 1
)

echo.
echo Instalando dependencias...
"%PYTHON_EXE%" -m pip install -r requirements.txt --quiet
if %ERRORLEVEL% neq 0 (
    echo Erro ao instalar dependencias.
    pause
    exit /b 1
)

echo.
echo Limpando build antigos...
if exist "build" rmdir /s /q "build" 2>nul
if exist "dist" rmdir /s /q "dist" 2>nul

echo.
echo Gerando executavel standalone...
"%PYTHON_EXE%" -m PyInstaller --noconfirm --onefile --windowed ^
  --icon "LOGO.ico" ^
  --name "StampaSaaS" ^
  --add-data "LOGO_BARRA DE TAREFAS.png;." ^
  --add-data "LOGO.ico;." ^
  --add-data "setup_app.py;." ^
  --add-data "updater.py;." ^
  --hidden-import=tkinter ^
  --hidden-import=sqlite3 ^
  --hidden-import=pandas ^
  --hidden-import=google.generativeai ^
  main_standalone.py

if %ERRORLEVEL% neq 0 (
    echo Erro na criacao do executavel.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo ========================================
echo SUCESSO! Executavel gerado:
echo   dist\StampaSaaS.exe
echo.
echo PRONTO PARA DISTRIBUIR!
echo Copie para qualquer computador.
echo Versoes antigas serao automaticamente
echo sobrescritas na atualizacao.
echo ========================================
pause
endlocal
