@echo off
setlocal EnableExtensions
title Uninstall Film Lab
cd /d "%~dp0"
set "ROOT=%CD%"

echo.
echo  UNINSTALL FILM LAB
echo  Removes the Desktop / Start Menu shortcuts.
echo  You can also delete this install folder.
echo  Close the Film Lab windows first.
echo.
echo  1  Remove shortcuts only          ^(keep files — Grok Bot can still patch^)
echo  2  Remove shortcuts AND this folder
echo  Q  Quit
echo.
set "PICK="
set /p PICK=Choose 1 or 2: 
if /I "%PICK%"=="Q" goto :eof
if "%PICK%"=="2" goto wipe
goto shortcuts

:shortcuts
cscript //nologo "%ROOT%\scripts\remove_desktop_shortcut.vbs"
echo Shortcuts removed. Files stay at %ROOT%
if "%~1"=="" pause
goto :eof

:wipe
if not exist "%ROOT%\app.py" (
    echo This does not look like a Film Lab folder. Refusing to delete.
    pause
    exit /b 1
)
if not exist "%ROOT%\START_FILM_LAB.bat" (
    echo START_FILM_LAB.bat missing. Refusing to delete.
    pause
    exit /b 1
)
if /I "%ROOT%"=="%USERPROFILE%" goto refuse
if /I "%ROOT%"=="%USERPROFILE%\Desktop" goto refuse
if /I "%ROOT%"=="%LOCALAPPDATA%" goto refuse
if exist "%ROOT%\.git" (
    echo This folder has a .git directory ^(source checkout^).
    echo Shortcuts will be removed. The folder is kept so Grok Bot can patch in place.
    echo To delete a git checkout, remove it yourself in Explorer.
    cscript //nologo "%ROOT%\scripts\remove_desktop_shortcut.vbs"
    pause
    goto :eof
)
echo Type DELETE to remove %ROOT%
set "CONFIRM="
set /p CONFIRM=
if /I not "%CONFIRM%"=="DELETE" (
    echo Cancelled.
    pause
    goto :eof
)
cscript //nologo "%ROOT%\scripts\remove_desktop_shortcut.vbs"
set "VICTIM=%ROOT%"
cd /d "%TEMP%"
echo Deleting %VICTIM% ...
rmdir /s /q "%VICTIM%"
echo Film Lab uninstalled.
pause
goto :eof

:refuse
echo Refusing to delete %ROOT%
pause
exit /b 1
