$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    . .\.venv\Scripts\Activate.ps1
} elseif (Test-Path ".\venv\Scripts\Activate.ps1") {
    . .\venv\Scripts\Activate.ps1
}

$env:FILM_LAB_PORT = $(if ($env:FILM_LAB_PORT) { $env:FILM_LAB_PORT } else { "43123" })
$env:FILM_LAB_HOST = $(if ($env:FILM_LAB_HOST) { $env:FILM_LAB_HOST } else { "127.0.0.1" })
Write-Host ""
Write-Host "Starting Film Lab (Gradio). This is the PROGRAM, not the source listing." -ForegroundColor Yellow
Write-Host "Works offline for local generation. Prefer START_FILM_LAB.bat (Comfy GPU1 + desk + browser). No PowerShell needed." -ForegroundColor Green
Write-Host "When it says Running on local URL, open Chrome or Edge:" -ForegroundColor Green
Write-Host "  http://127.0.0.1:43123"
Write-Host "Cursor Open in Web / Origin agent URL is CODE ONLY. Leave this window open."
Write-Host "Primary generate: Local AMD img2vid (needs ComfyUI on 127.0.0.1:8188)."
Write-Host "Ken Burns is CPU fallback. No Film Lab credits. Online optional: Grok / Gemini / ChatGPT / Claude / ElevenLabs."
Write-Host ""
if (Get-Command python -ErrorAction SilentlyContinue) {
    python app.py
} else {
    py -3 app.py
}
