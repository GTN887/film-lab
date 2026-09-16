@echo off
setlocal EnableExtensions
title Install Film Lab
cd /d "%~dp0"
set "ROOT=%CD%"
set "DEST_DESK=%USERPROFILE%\Desktop\Film Lab"
set "DEST_APP=%LOCALAPPDATA%\Film Lab"

echo.
echo  INSTALL FILM LAB
echo  Places app files + Desktop / Start Menu shortcuts ^(purple FL icon^).
echo  Works offline for local generation. No Film Lab credits. No PowerShell.
echo  After install, Grok Bot / Cursor can patch files in the install folder.
echo.
echo  1  Install to Desktop\Film Lab   ^(files + shortcuts^)
echo  2  Install to AppData\Local\Film Lab
echo  3  Use this folder               ^(patch in place — keep files here^)
echo  Q  Quit
echo.
set "PICK="
set /p PICK=Choose 1, 2, or 3: 
if /I "%PICK%"=="Q" goto :eof
if "%PICK%"=="2" (
    set "DEST=%DEST_APP%"
    goto copy_files
)
if "%PICK%"=="3" goto pin
set "DEST=%DEST_DESK%"

:copy_files
if /I "%ROOT%"=="%DEST%" (
    echo Already in the install folder — pinning shortcuts only.
    goto pin
)
echo Copying Film Lab files to %DEST% ...
if not exist "%DEST%" mkdir "%DEST%"
robocopy "%ROOT%" "%DEST%" /E /XD .git .venv venv __pycache__ .gradio .cursor data\logs data\projects data\models /XF *.pyc *.mp4 .env /NFL /NDL /NJH /NJS /NP
if errorlevel 8 (
    echo Copy failed.
    pause
    exit /b 1
)
if exist "%ROOT%\data\characters" (
    if not exist "%DEST%\data\characters" mkdir "%DEST%\data\characters"
    robocopy "%ROOT%\data\characters" "%DEST%\data\characters" /E /XD refs __pycache__ /NFL /NDL /NJH /NJS /NP
)
set "ROOT=%DEST%"
cd /d "%ROOT%"
echo Files placed at %DEST%

:pin
call :install_packages
if errorlevel 1 (
    echo Python packages failed. Install Python 3.11+ from python.org ^(Add to PATH^), then run this again.
    pause
    exit /b 1
)
if exist "%ROOT%\assets\film_lab.ico" (
    echo [.ShellClassInfo]> "%ROOT%\desktop.ini"
    echo IconResource=assets\film_lab.ico,0>> "%ROOT%\desktop.ini"
    attrib +s "%ROOT%" >nul 2>&1
    attrib +h +s "%ROOT%\desktop.ini" >nul 2>&1
)
cscript //nologo "%ROOT%\scripts\make_desktop_shortcut.vbs" "%ROOT%"
if errorlevel 1 (
    echo Shortcut helper failed. The program is still at %ROOT%
    echo Daily start: double-click START_FILM_LAB.bat
    pause
    exit /b 1
)
echo.
echo  Installed. Double-click Film Lab on the Desktop ^(purple FL icon^).
echo  Or START_FILM_LAB.bat — browser: http://127.0.0.1:43123
echo  Start Menu: Film Lab. Uninstall: UNINSTALL_FILM_LAB.bat
echo  Local Gradio: http://127.0.0.1:43123
echo  Patch in place: point Grok Bot / Cursor at %ROOT%
echo.
pause
goto :eof

:install_packages
if exist "%ROOT%\.venv\Scripts\python.exe" (
    echo Python venv already present.
    exit /b 0
)
where py >nul 2>&1
if errorlevel 1 (
    where python >nul 2>&1
    if errorlevel 1 (
        echo Need Python 3.11+ from https://www.python.org/downloads/
        echo Tick Add python.exe to PATH.
        exit /b 1
    )
    echo Creating .venv with python ...
    python -m venv "%ROOT%\.venv"
) else (
    echo Creating .venv with py -3 ...
    py -3 -m venv "%ROOT%\.venv"
)
if not exist "%ROOT%\.venv\Scripts\python.exe" exit /b 1
"%ROOT%\.venv\Scripts\python.exe" -m pip install --upgrade pip
"%ROOT%\.venv\Scripts\python.exe" -m pip install -r "%ROOT%\requirements.txt"
where ffmpeg >nul 2>&1
if errorlevel 1 (
    echo ffmpeg is not on PATH. Ken Burns / stitch need it.
    echo Install: winget install Gyan.FFmpeg   ^(new terminal after^)
)
echo Packages ready. Works offline for local generation.
exit /b 0
