@echo off
setlocal
cd /d "%~dp0"
title LinguaLive - Windows setup and launcher
set "VENV=%~dp0.venv-windows"
if exist "%VENV%\Scripts\python.exe" goto checkenv
where py >nul 2>&1
if errorlevel 1 goto nopython
for %%V in (3.13 3.12 3.11) do (
    py -%%V -c "import struct,tkinter; assert struct.calcsize('P') == 8" >nul 2>&1
    if not errorlevel 1 (
        echo Creating private Python %%V environment...
        py -%%V -m venv "%VENV%"
        if errorlevel 1 goto fail
        goto checkenv
    )
)
goto nopython
:checkenv
set "PY=%VENV%\Scripts\python.exe"
"%PY%" -c "import sys,struct,tkinter; assert (3,11) <= sys.version_info[:2] <= (3,13) and struct.calcsize('P') == 8" 
if errorlevel 1 goto fail
"%PY%" -c "import numpy, scipy, faster_whisper, pyaudiowpatch" >nul 2>&1
if not errorlevel 1 goto launch
 echo Installing dependencies from PyPI. Internet connection required.
"%PY%" -m pip install --upgrade pip
if errorlevel 1 goto fail
"%PY%" -m pip install --only-binary=:all: -r requirements.txt
if errorlevel 1 goto fail
:launch
"%PY%" japanese_live_captions.py %*
if errorlevel 1 goto fail
exit /b 0
:nopython
echo Please install 64-bit Python 3.13, 3.12 or 3.11 with the Python launcher.
echo Official download: https://www.python.org/downloads/
goto fail
:fail
echo.
echo Setup or launch failed. Copy the error above. See README.md for help.
pause
exit /b 1
