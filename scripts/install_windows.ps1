# Film Lab — Windows setup (Python 3.11+ and ffmpeg required).
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
. "$PSScriptRoot\_python.ps1"

Write-Host "Film Lab installer" -ForegroundColor Yellow
Write-Host "LOCAL ONLY — adult film-school stills stay on this machine." -ForegroundColor DarkYellow
Write-Host "No Film Lab credits. Primary motion is local AMD img2vid (ComfyUI)."

$py = Get-FilmLabPython
if (-not $py) {
    Write-Error @"
Need a real Python 3.11+ (not the Microsoft Store stub named python).
Install from https://www.python.org/downloads/ and tick Add python.exe to PATH.
On this desk: py -3  (3.14 is OK for Film Lab; ComfyUI sidecar wants 3.12).
"@
}

Write-Host "Python $($py.Version) — $($py.Exe)"

if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    Write-Host "ffmpeg is not on PATH." -ForegroundColor Red
    Write-Host "Install it, then open a new terminal:"
    Write-Host "  winget install Gyan.FFmpeg"
    Write-Host "  or  choco install ffmpeg"
    Write-Host "Ken Burns fallback and stitch will not run until ffmpeg is available."
} else {
    ffmpeg -version | Select-Object -First 1
}

if (-not (Test-Path ".\.venv")) {
    Write-Host "Creating .venv ..."
    Invoke-FilmLabPython -Python $py -Arguments @("-m", "venv", ".venv")
}

. .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

Write-Host ""
Write-Host "Done. Works offline for local generation. Read START_HERE.md, then:" -ForegroundColor Green
Write-Host "  Double-click INSTALL_FILM_LAB.bat  (Install Film Lab on Desktop)"
Write-Host "  Daily: START_FILM_LAB.bat or the Film Lab icon. No PowerShell."
Write-Host "  Repair (offline):       REPAIR.bat"
Write-Host "Open Chrome/Edge:  http://127.0.0.1:43123"
Write-Host "Cursor Open in Web / agent URL is source code only — not this UI."
Write-Host ""
Write-Host "AMD img2vid (RX 5600 XT) — install the sidecar, then start it in a second window:"
Write-Host "  powershell -ExecutionPolicy Bypass -File .\scripts\install_comfyui_amd.ps1"
Write-Host "  powershell -ExecutionPolicy Bypass -File .\scripts\run_comfyui_amd.ps1"
Write-Host "  .\scripts\check_amd.ps1"
Write-Host "Ken Burns is CPU fallback only. No CUDA on this machine."
Write-Host "Optional Writing Studio keys (yours — no Film Lab credits):"
Write-Host "  `$env:FILM_LAB_XAI_API_KEY = 'xai-...'"
Write-Host "  `$env:FILM_LAB_GEMINI_API_KEY = 'AIza...'"
Write-Host "  `$env:FILM_LAB_OPENAI_API_KEY = 'sk-...'"
Write-Host "  `$env:FILM_LAB_OPENAI_MODEL = 'gpt-4.1'   # optional; fail-soft if retired"
