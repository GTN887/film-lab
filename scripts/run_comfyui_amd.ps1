# Start the local ComfyUI sidecar for Film Lab img2vid (SVD-XT).
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

$desktop = Join-Path $env:LOCALAPPDATA "Comfy-Desktop\ComfyUI-Installs\ComfyUI\ComfyUI"
$legacy = if ($env:FILM_LAB_COMFY_HOME) { $env:FILM_LAB_COMFY_HOME } else { Join-Path $env:USERPROFILE "FilmLab-ComfyUI" }

if ($env:FILM_LAB_COMFY_HOME -and (Test-Path (Join-Path $env:FILM_LAB_COMFY_HOME "main.py"))) {
    $sidecar = $env:FILM_LAB_COMFY_HOME
} elseif (Test-Path (Join-Path $desktop "main.py")) {
    $sidecar = $desktop
} elseif (Test-Path (Join-Path $legacy "main.py")) {
    $sidecar = $legacy
} else {
    Write-Error "ComfyUI not found. Expected Comfy-Desktop at $desktop or FilmLab-ComfyUI at $legacy."
}

$port = if ($env:FILM_LAB_COMFY_PORT) { $env:FILM_LAB_COMFY_PORT } else { "8188" }
$device = if ($env:FILM_LAB_COMFY_CUDA_DEVICE) { $env:FILM_LAB_COMFY_CUDA_DEVICE } else { "1" }
Set-Location $sidecar
if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    . .\.venv\Scripts\Activate.ps1
}

$svd = Join-Path $sidecar "models\checkpoints\svd_xt.safetensors"
if (Test-Path $svd) {
    Write-Host "SVD-XT: $svd" -ForegroundColor Green
} else {
    Write-Host "SVD-XT missing at $svd — put svd_xt.safetensors in models\checkpoints." -ForegroundColor Yellow
}

Write-Host "Starting ComfyUI on 127.0.0.1:$port --cuda-device $device (RX 5600 XT)" -ForegroundColor Yellow
Write-Host "Leave this window open. Film Lab talks to it — nothing is uploaded."
Write-Host "No Film Lab credits. No Film Lab NSFW filter. Adults 18+ only."
Write-Host ""

python main.py --cuda-device $device --lowvram --listen 127.0.0.1 --port $port --disable-auto-launch
