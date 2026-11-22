@echo off
rem Odwołania2JSON: instalacja i uruchomienie jednym poleceniem (Windows): start.bat
rem Tworzy .venv (Python 3.13+), instaluje zależności, przetwarza input\ -> output\.
setlocal
cd /d "%~dp0"
chcp 65001 >nul
set PYTHONUTF8=1

if not defined PYTHON set PYTHON=py -3.13
%PYTHON% -c "import sys; sys.exit(0 if sys.version_info >= (3, 13) else 1)" 2>nul
if errorlevel 1 (
    echo błąd: potrzebny Python 3.13+ ^(zainstaluj go albo ustaw zmienną PYTHON na python.exe^) 1>&2
    exit /b 2
)

if not exist ".venv\Scripts\python.exe" (
    %PYTHON% -m venv .venv || exit /b 1
)
".venv\Scripts\python.exe" -m pip install --quiet --disable-pip-version-check -r requirements.txt || exit /b 1

if not exist input mkdir input
if not exist output mkdir output

rem Klucz LLM podaj zmienną środowiskową (nigdy w repozytorium ani w plikach śledzonych przez Git):
rem   set LLM_API_KEY=...  set LLM_BASE_URL=https://adres-api/v1  set LLM_MODEL=nazwa-modelu
if not defined LLM_API_KEY echo uwaga: brak LLM_API_KEY; ustaw LLM_API_KEY, LLM_BASE_URL i LLM_MODEL ^(klucz trzymamy poza Git^). 1>&2

".venv\Scripts\python.exe" -m odwolania2json process input output
exit /b %ERRORLEVEL%
