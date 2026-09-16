@echo off
setlocal EnableExtensions
title Film Lab
cd /d "%~dp0"
set "ROOT=%CD%"
if not defined FILM_LAB_PORT set "FILM_LAB_PORT=43123"
if not defined FILM_LAB_HOST set "FILM_LAB_HOST=127.0.0.1"
if not defined FILM_LAB_COMFY_PORT set "FILM_LAB_COMFY_PORT=8188"
if not defined FILM_LAB_COMFY_CUDA_DEVICE set "FILM_LAB_COMFY_CUDA_DEVICE=1"

echo.
echo  FILM LAB — PRE-FINISH
echo  Works offline for local generation.
echo  Local Gradio: http://%FILM_LAB_HOST%:%FILM_LAB_PORT%
echo  No PowerShell. Close the Film Lab window to stop.
echo.

if not exist "%ROOT%\data\logs" mkdir "%ROOT%\data\logs"
>>"%ROOT%\data\logs\launcher.log" echo %DATE% %TIME% START_FILM_LAB

if not exist "%ROOT%\app.py" (
    echo app.py missing. Run INSTALL_FILM_LAB.bat from the Film Lab folder.
    pause
    exit /b 1
)

call :port_open %FILM_LAB_COMFY_PORT%
if errorlevel 1 (
    echo Comfy %FILM_LAB_COMFY_PORT% is Off — starting sidecar on GPU1 if installed.
    start "Film Lab Comfy" /D "%ROOT%" cmd /k call "%ROOT%\scripts\run_comfyui_amd.bat"
) else (
    echo Comfy already listening on %FILM_LAB_COMFY_PORT%.
)

call :port_open %FILM_LAB_PORT%
if errorlevel 1 (
    echo Film Lab %FILM_LAB_PORT% is Off — starting desk.
    start "Film Lab" /D "%ROOT%" cmd /k call "%ROOT%\scripts\run_film_lab.bat"
) else (
    echo Film Lab already listening on %FILM_LAB_PORT%.
)

echo Waiting for http://%FILM_LAB_HOST%:%FILM_LAB_PORT% ...
set /a _i=0
:wait_lab
call :port_open %FILM_LAB_PORT%
if not errorlevel 1 goto open_ui
set /a _i+=1
if %_i% GEQ 50 goto no_ui
timeout /t 1 /nobreak >nul
goto wait_lab

:open_ui
start "" "http://%FILM_LAB_HOST%:%FILM_LAB_PORT%"
echo Opened the local UI. Leave the Film Lab window open.
echo Repair: REPAIR.bat
goto :eof

:no_ui
echo Desk did not bind %FILM_LAB_PORT% yet.
echo Leave the Film Lab window open, then open http://%FILM_LAB_HOST%:%FILM_LAB_PORT%
echo Repair: double-click REPAIR.bat
pause
goto :eof

:port_open
netstat -ano 2>nul | findstr /C:":%~1" | findstr /C:"LISTENING" >nul
if errorlevel 1 exit /b 1
exit /b 0
