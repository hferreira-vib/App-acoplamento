@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Dimensionamento de Acoplamentos Industriais

echo ============================================================
echo    Dimensionamento de Acoplamentos Industriais
echo ============================================================
echo.

REM --- Verifica se o Python esta instalado ---
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao foi encontrado no sistema.
    echo Instale o Python em https://www.python.org/downloads/
    echo e marque a opcao "Add Python to PATH" durante a instalacao.
    echo.
    pause
    exit /b 1
)

echo [1/2] A verificar/instalar dependencias (streamlit, pandas)...
python -m pip install -r requirements.txt --quiet --disable-pip-version-check

echo [2/2] A iniciar a aplicacao no navegador...
echo (Para fechar a aplicacao, feche esta janela ou pressione Ctrl+C)
echo.
python -m streamlit run app.py

pause
