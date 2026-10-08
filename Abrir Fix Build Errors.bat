@echo off
REM Abre a interface grafica com um duplo clique, sem janela de terminal.
REM Este arquivo precisa ficar na MESMA PASTA que fix_build_errors_gui.py

set SCRIPT_DIR=%~dp0
set SCRIPT_PATH=%SCRIPT_DIR%fix_build_errors_gui.py

where pythonw >nul 2>nul
if %ERRORLEVEL%==0 (
    start "" pythonw "%SCRIPT_PATH%"
) else (
    where python >nul 2>nul
    if %ERRORLEVEL%==0 (
        start "" python "%SCRIPT_PATH%"
    ) else (
        echo Python nao foi encontrado no PATH deste computador.
        echo Instale o Python em https://www.python.org/downloads/ e marque a opcao "Add Python to PATH" durante a instalacao.
        pause
    )
)
