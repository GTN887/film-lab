@echo off
setlocal EnableExtensions
rem Stop whatever is LISTENING on the given TCP port. No PowerShell.
if "%~1"=="" exit /b 1
set "PORT=%~1"
set "KILLED=0"
for /f "tokens=5" %%P in ('netstat -ano 2^>nul ^| findstr /C:":%PORT%" ^| findstr /C:"LISTENING"') do (
    if not "%%P"=="0" (
        taskkill /F /PID %%P >nul 2>&1
        set /a KILLED+=1
    )
)
echo Kill port %PORT% (stopped listener^(s^)).
exit /b 0
