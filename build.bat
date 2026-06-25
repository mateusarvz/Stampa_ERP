@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

REM ============================================
REM STAMPA SAAS - BUILD EXECUTAVEL
REM Lógica nova. Simples e eficiente.
REM ============================================

echo.
echo [*] Fechando versoes anteriores...
taskkill /f /im StampaSaaS.exe 2>nul

echo [*] Detectando Python...
set PYTHON_EXE=python.exe
if exist ".venv_stampa\Scripts\python.exe" (
    set PYTHON_EXE=.venv_stampa\Scripts\python.exe
)

"%PYTHON_EXE%" --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo.
    echo [!] ERRO: Python nao encontrado
    echo [!] Instale Python 3.9+ ou ative venv
    pause
    exit /b 1
)

echo [*] Instalando dependencias...
"%PYTHON_EXE%" -m pip install -q -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo [!] Erro ao instalar dependencias
    pause
    exit /b 1
)

echo [*] Limpando builds antigos...
if exist "build" rmdir /s /q "build" 2>nul
if exist "dist" rmdir /s /q "dist" 2>nul
if exist "__pycache__" rmdir /s /q "__pycache__" 2>nul

echo [*] Gerando executavel com PyInstaller...
"%PYTHON_EXE%" -m PyInstaller --noconfirm ^
  --onefile ^
  --windowed ^
  --icon="LOGO.ico" ^
  --name="StampaSaaS" ^
  --add-data="LOGO.ico;." ^
  --add-data="LOGO_BARRA DE TAREFAS.png;." ^
  --hidden-import=tkinter ^
  --hidden-import=sqlite3 ^
  --hidden-import=pandas ^
  --hidden-import=google.generativeai ^
  --hidden-import=dotenv ^
  --hidden-import=matplotlib ^
  --hidden-import=requests ^
  main.py

if %ERRORLEVEL% neq 0 (
    echo [!] Erro ao gerar executavel
    pause
    exit /b 1
)

echo.
echo [+] SUCESSO!
echo [+] Executavel: dist\StampaSaaS.exe
echo [+] Pronto para usar!
echo.
pause
