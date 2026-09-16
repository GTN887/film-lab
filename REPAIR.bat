@echo off
setlocal EnableExtensions
title Film Lab Repair
cd /d "%~dp0"
set "ROOT=%CD%"
if not defined FILM_LAB_PORT set "FILM_LAB_PORT=43123"
if not defined FILM_LAB_HOST set "FILM_LAB_HOST=127.0.0.1"
if not defined FILM_LAB_COMFY_PORT set "FILM_LAB_COMFY_PORT=8188"
if not exist "%ROOT%\data\logs" mkdir "%ROOT%\data\logs"

if /I "%~1"=="restart-lab" goto restart_lab
if /I "%~1"=="restart-comfy" goto restart_comfy
if /I "%~1"=="kill-ports" goto kill_ports
if /I "%~1"=="logs" goto logs
if /I "%~1"=="safe" goto safe

:menu
echo.
echo  FILM LAB  —  Repair (offline)
echo  Works offline for local generation. No PowerShell.
echo.
echo   1  Restart Film Lab
echo   2  Restart Comfy (GPU1)
echo   3  Kill ports 43123 / 8188
echo   4  Open logs
echo   5  Safe mode (480p / short clip) then START
echo   Q  Quit
echo.
set "PICK="
set /p PICK=Choose: 
if /I "%PICK%"=="Q" goto :eof
if "%PICK%"=="1" goto restart_lab
if "%PICK%"=="2" goto restart_comfy
if "%PICK%"=="3" goto kill_ports
if "%PICK%"=="4" goto logs
if "%PICK%"=="5" goto safe
goto :eof

:kill_ports
call "%ROOT%\scripts\kill_port.bat" %FILM_LAB_PORT%
call "%ROOT%\scripts\kill_port.bat" %FILM_LAB_COMFY_PORT%
echo Ports cleared.
if "%~1"=="" pause
goto :eof

:restart_lab
call "%ROOT%\scripts\kill_port.bat" %FILM_LAB_PORT%
timeout /t 1 /nobreak >nul
start "Film Lab" /D "%ROOT%" cmd /k call "%ROOT%\scripts\run_film_lab.bat"
echo Waiting for http://%FILM_LAB_HOST%:%FILM_LAB_PORT% ...
set /a _i=0
:wait_lab
netstat -ano 2>nul | findstr /C:":%FILM_LAB_PORT%" | findstr /C:"LISTENING" >nul
if not errorlevel 1 (
    start "" "http://%FILM_LAB_HOST%:%FILM_LAB_PORT%"
    goto :eof
)
set /a _i+=1
if %_i% GEQ 40 goto :eof
timeout /t 1 /nobreak >nul
goto wait_lab

:restart_comfy
call "%ROOT%\scripts\kill_port.bat" %FILM_LAB_COMFY_PORT%
timeout /t 1 /nobreak >nul
start "Film Lab Comfy" /D "%ROOT%" cmd /k call "%ROOT%\scripts\run_comfyui_amd.bat"
goto :eof

:logs
echo Logs: %ROOT%\data\logs
start "" "%ROOT%\data\logs"
goto :eof

:safe
if not exist "%ROOT%\data" mkdir "%ROOT%\data"
echo 480p / 5s> "%ROOT%\data\safe_mode.flag"
set "FILM_LAB_SAFE_MODE=1"
>>"%ROOT%\data\logs\launcher.log" echo %DATE% %TIME% Safe mode on
call "%ROOT%\scripts\kill_port.bat" %FILM_LAB_PORT%
timeout /t 1 /nobreak >nul
start "Film Lab" /D "%ROOT%" cmd /k "set FILM_LAB_SAFE_MODE=1&& call "%ROOT%\scripts\run_film_lab.bat""
echo Safe mode (480p / short clip). Starting desk.
goto :eof
