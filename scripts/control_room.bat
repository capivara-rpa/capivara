@echo off
rem Sobe a Control Room (orquestrador + painel de trace) - Windows
rem   scripts\control_room.bat              -> sobe a Control Room
rem   scripts\control_room.bat --exemplos   -> popula os exemplos e sobe

setlocal
set ROOT=%~dp0..
cd /d "%ROOT%"

if not exist ".venv" (
    echo Ambiente virtual nao encontrado. Rode primeiro: scripts\install.bat
    exit /b 1
)

call .venv\Scripts\activate.bat

if "%~1"=="--exemplos" (
    python -m core.control_room.dados_exemplo
    shift
)

python -m core.control_room.servidor %*
