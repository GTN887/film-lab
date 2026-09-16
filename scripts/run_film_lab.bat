@echo off
setlocal EnableExtensions
title Film Lab
cd /d "%~dp0\.."
if not defined FILM_LAB_PORT set "FILM_LAB_PORT=43123"
if not defined FILM_LAB_HOST set "FILM_LAB_HOST=127.0.0.1"
echo.
echo Starting Film Lab (Gradio). This is the PROGRAM, not the source listing.
echo Works offline for local generation.
echo When it says Running on local URL, Chrome / Edge:
echo   http://%FILM_LAB_HOST%:%FILM_LAB_PORT%
echo Leave this window open. Close it to stop the desk.
echo.
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" app.py
) else (
    py -3 app.py
)
if errorlevel 1 (
    echo Film Lab exited with an error. Try REPAIR.bat or INSTALL_FILM_LAB.bat.
    pause
)
