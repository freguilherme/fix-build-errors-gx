@echo off
REM =========================================================================
REM  Gera um .exe standalone (que roda sem precisar de Python instalado)
REM  a partir de fix_build_errors_gui.py
REM
REM  RODE ESTE ARQUIVO SOMENTE UMA VEZ, numa maquina que TEM Python instalado.
REM  O resultado (o .exe) fica em uma pasta "dist" e pode ser copiado pra
REM  qualquer outro computador, sem precisar instalar Python la.
REM
REM  Este arquivo precisa ficar na MESMA PASTA que fix_build_errors_gui.py
REM =========================================================================

set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

where python >nul 2>nul
if not %ERRORLEVEL%==0 (
    echo Python nao foi encontrado no PATH desta maquina.
    echo Instale o Python em https://www.python.org/downloads/ e marque
    echo "Add Python to PATH" durante a instalacao, depois rode este arquivo de novo.
    pause
    exit /b 1
)

echo Instalando PyInstaller (se ja estiver instalado, so confirma a versao)...
python -m pip install --upgrade pyinstaller

echo.
echo Gerando o executavel standalone...
python -m PyInstaller --onefile --windowed --name "FixBuildErrors" fix_build_errors_gui.py

echo.
if exist "dist\FixBuildErrors.exe" (
    echo =========================================================
    echo  Pronto! O executavel esta em:
    echo  %SCRIPT_DIR%dist\FixBuildErrors.exe
    echo.
    echo  Copie esse arquivo .exe para qualquer computador e ele
    echo  vai rodar direto, sem precisar instalar Python.
    echo =========================================================
) else (
    echo Algo deu errado na geracao do .exe. Veja as mensagens acima.
)

pause
