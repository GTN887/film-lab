# Film Lab desktop START — Comfy on GPU1 + desk + local UI.
# Works offline once models are installed. No folder hunting after the shortcut.
$ErrorActionPreference = "Stop"
. "$PSScriptRoot\_common.ps1"

$root = Get-FilmLabRoot
Set-Location $root
$env:FILM_LAB_PORT = "$(Get-FilmLabPort)"
$env:FILM_LAB_HOST = "127.0.0.1"
if (-not $env:FILM_LAB_COMFY_CUDA_DEVICE) { $env:FILM_LAB_COMFY_CUDA_DEVICE = "1" }

Write-Host ""
Write-Host "FILM LAB  —  Offline-first desktop start" -ForegroundColor Yellow
Write-Host "Works offline for local generation. Online optional: Grok / Gemini / ChatGPT / Claude / ElevenLabs."
Write-Host "No Film Lab credits. Adults 18+."
Write-Host ""

$comfyPort = Get-ComfyPort
$labPort = Get-FilmLabPort

if (-not (Test-FilmLabPortOpen -Port $comfyPort)) {
    Write-FilmLabLog "Comfy $comfyPort is Off — starting sidecar on GPU1."
    Start-FilmLabComfyWindow
} else {
    Write-FilmLabLog "Comfy already listening on $comfyPort."
}

if (-not (Test-FilmLabPortOpen -Port $labPort)) {
    Write-FilmLabLog "Film Lab $labPort is Off — starting desk."
    Start-FilmLabAppWindow
} else {
    Write-FilmLabLog "Film Lab already listening on $labPort."
}

Write-Host "Waiting for http://127.0.0.1:$labPort ..."
if (Wait-FilmLabPort -Port $labPort -Seconds 50) {
    Start-Process "http://127.0.0.1:$labPort"
    Write-FilmLabLog "Opened local UI."
} else {
    Write-FilmLabLog "Desk did not bind $labPort yet. Leave the Film Lab window open, then open http://127.0.0.1:$labPort"
    Write-Host "Repair: double-click REPAIR.bat  (Restart Film Lab / Kill ports / Open logs)" -ForegroundColor DarkYellow
}

Write-Host ""
Write-Host "Comfy + Film Lab stay in their windows. Close those windows to stop." -ForegroundColor Green
Write-Host "Works offline for local generation."
