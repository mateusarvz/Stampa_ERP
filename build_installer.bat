@echo off
setlocal
if not exist "dist\StampaSaaS.exe" (
    echo Erro: arquivo dist\StampaSaaS.exe nao encontrado.
    echo Execute build_exe.bat primeiro.
    pause
    exit /b 1
)
where ISCC >nul 2>nul
if errorlevel 1 (
    echo Erro: Inno Setup Compiler (ISCC) nao encontrado no PATH.
    echo Instale o Inno Setup e adicione-o ao PATH para gerar o instalador.
    pause
    exit /b 1
)
ISCC StampaSaaSInstaller.iss
if %ERRORLEVEL% neq 0 (
    echo Erro ao gerar o instalador.
    pause
    exit /b %ERRORLEVEL%
)
echo Instalador gerado com sucesso.
pause
endlocal
