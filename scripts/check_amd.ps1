# Probe Windows AMD + ComfyUI sidecar for Film Lab.
$ErrorActionPreference = "Continue"
Set-Location (Split-Path -Parent $PSScriptRoot)
. "$PSScriptRoot\_python.ps1"

Write-Host "Film Lab — AMD / ComfyUI check" -ForegroundColor Yellow

$gpu = Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name
Write-Host "GPU: $($gpu -join ', ')"
if ($gpu -match "5600 XT") {
    Write-Host "  RX 5600 XT detected — ComfyUI --cuda-device 1, SVD-XT at 512x288." -ForegroundColor Green
} elseif ($gpu -match "NVIDIA") {
    Write-Host "  NVIDIA visible. Film Lab still talks to the local ComfyUI sidecar."
} else {
    Write-Host "  Confirm this is an AMD Radeon with ~6GB if you expect the 512x288 path."
}

$py = Get-FilmLabPython
if ($py) {
    Write-Host "Python $($py.Version) — $($py.Exe)"
} else {
    Write-Host "Python: MISSING (Store stub does not count). Use py -3 from python.org." -ForegroundColor Red
}

if (Get-Command ffmpeg -ErrorAction SilentlyContinue) {
    ffmpeg -version | Select-Object -First 1
} else {
    Write-Host "ffmpeg: MISSING — winget install Gyan.FFmpeg" -ForegroundColor Red
}

$desktop = Join-Path $env:LOCALAPPDATA "Comfy-Desktop\ComfyUI-Installs\ComfyUI\ComfyUI"
$legacy = if ($env:FILM_LAB_COMFY_HOME) { $env:FILM_LAB_COMFY_HOME } else { Join-Path $env:USERPROFILE "FilmLab-ComfyUI" }
$sidecar = $null
foreach ($candidate in @($env:FILM_LAB_COMFY_HOME, $desktop, $legacy)) {
    if ($candidate -and (Test-Path (Join-Path $candidate "main.py"))) {
        $sidecar = $candidate
        break
    }
}
if ($sidecar) {
    Write-Host "ComfyUI tree: $sidecar"
    $svd = Join-Path $sidecar "models\checkpoints\svd_xt.safetensors"
    if (Test-Path $svd) { Write-Host "SVD-XT: $svd" -ForegroundColor Green } else { Write-Host "SVD-XT: missing ($svd)" -ForegroundColor Yellow }
} else {
    Write-Host "ComfyUI tree: missing — start Comfy-Desktop or run run_comfyui_amd.ps1" -ForegroundColor Red
}

$url = if ($env:FILM_LAB_COMFY_URL) { $env:FILM_LAB_COMFY_URL } else { "http://127.0.0.1:8188" }
try {
    $r = Invoke-WebRequest -Uri "$url/system_stats" -UseBasicParsing -TimeoutSec 5
    Write-Host "ComfyUI sidecar: Ready ($url) status $($r.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "ComfyUI sidecar: Off at $url — run .\scripts\run_comfyui_amd.ps1" -ForegroundColor Red
}

Write-Host "Film Lab credits: none"
Write-Host "Primary generate: local SVD-XT img2vid. Ken Burns is Advanced only."
