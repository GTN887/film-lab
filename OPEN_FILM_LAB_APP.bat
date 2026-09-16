@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Film Lab
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -m film_lab.native_desktop
) else (
  py -3 -m film_lab.native_desktop
)
if errorlevel 1 (
  echo.
  echo Film Lab could not start. Run INSTALL_FILM_LAB.bat once, then try again.
  pause
)
