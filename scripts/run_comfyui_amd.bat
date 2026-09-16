@echo off
setlocal EnableExtensions
title Film Lab Comfy
cd /d "%~dp0\.."
if not defined FILM_LAB_COMFY_PORT set "FILM_LAB_COMFY_PORT=8188"
if not defined FILM_LAB_COMFY_CUDA_DEVICE set "FILM_LAB_COMFY_CUDA_DEVICE=1"

set "COMFY="
if defined FILM_LAB_COMFY_HOME if exist "%FILM_LAB_COMFY_HOME%\main.py" set "COMFY=%FILM_LAB_COMFY_HOME%"
if not defined COMFY if exist "%LOCALAPPDATA%\Comfy-Desktop\ComfyUI-Installs\ComfyUI\ComfyUI\main.py" set "COMFY=%LOCALAPPDATA%\Comfy-Desktop\ComfyUI-Installs\ComfyUI\ComfyUI"
if not defined COMFY if exist "%USERPROFILE%\FilmLab-ComfyUI\main.py" set "COMFY=%USERPROFILE%\FilmLab-ComfyUI"

if not defined COMFY (
    echo ComfyUI sidecar not found.
    echo Film Lab still runs. Animate needs the sidecar on 127.0.0.1:%FILM_LAB_COMFY_PORT%.
    echo Expected: %%LOCALAPPDATA%%\Comfy-Desktop\...\ComfyUI  or  %%USERPROFILE%%\FilmLab-ComfyUI
    echo First-time sidecar: scripts\install_comfyui_amd.ps1
    goto :eof
)

cd /d "%COMFY%"
if exist "models\checkpoints\svd_xt.safetensors" (
    echo SVD-XT: models\checkpoints\svd_xt.safetensors
) else (
    echo SVD-XT missing — put svd_xt.safetensors in models\checkpoints.
)

echo Starting ComfyUI on 127.0.0.1:%FILM_LAB_COMFY_PORT% --cuda-device %FILM_LAB_COMFY_CUDA_DEVICE%
echo Leave this window open. Nothing is uploaded. No Film Lab credits.
echo.

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" main.py --cuda-device %FILM_LAB_COMFY_CUDA_DEVICE% --lowvram --listen 127.0.0.1 --port %FILM_LAB_COMFY_PORT% --disable-auto-launch
) else (
    py -3 main.py --cuda-device %FILM_LAB_COMFY_CUDA_DEVICE% --lowvram --listen 127.0.0.1 --port %FILM_LAB_COMFY_PORT% --disable-auto-launch
)
if errorlevel 1 pause
