# Film Lab — ComfyUI sidecar for AMD Radeon (DirectML, ~6GB).
# RX 5600 XT / Windows 11. Open weights only. No Film Lab credits.
param(
    [switch]$DownloadModels
)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
. "$PSScriptRoot\_python.ps1"

Write-Host "Film Lab — ComfyUI AMD sidecar" -ForegroundColor Yellow
Write-Host "Target: Radeon RX 5600 XT (~6GB) via DirectML. No CUDA. No paid Higgsfield API." -ForegroundColor DarkYellow

$py = Get-FilmLabPython -Prefer312
if (-not $py) {
    Write-Error @"
Need a real Python 3.11 or 3.12 (not the Microsoft Store stub).
ComfyUI + torch-directml are not reliable on Python 3.14.
Install 3.12 from https://www.python.org/downloads/ — tick Add python.exe to PATH.
Then: py -3.12 --version
"@
}

if ([version]$py.Version -ge [version]"3.13") {
    Write-Host "WARNING: Python $($py.Version) detected. Prefer 3.12 for torch-directml / ComfyUI." -ForegroundColor Red
    Write-Host "Install Python 3.12 and re-run this script if pip fails." -ForegroundColor Red
}

Write-Host "Using Python $($py.Version) at $($py.Exe)"

$sidecar = Join-Path $env:USERPROFILE "FilmLab-ComfyUI"
if (-not (Test-Path $sidecar)) {
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        Write-Error "git is required to clone ComfyUI. Install Git for Windows, then re-run."
    }
    Write-Host "Cloning ComfyUI → $sidecar"
    git clone --depth 1 https://github.com/comfyanonymous/ComfyUI.git $sidecar
} else {
    Write-Host "ComfyUI already at $sidecar"
}

Push-Location $sidecar
try {
    if (-not (Test-Path ".\.venv")) {
        Write-Host "Creating ComfyUI .venv ..."
        Invoke-FilmLabPython -Python $py -Arguments @("-m", "venv", ".venv")
    }
    . .\.venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    Write-Host "Installing torch-directml (AMD DirectML, not CUDA) ..."
    python -m pip install torch-directml
    if (Test-Path ".\requirements.txt") {
        python -m pip install -r requirements.txt
    }

    $custom = Join-Path $sidecar "custom_nodes"
    New-Item -ItemType Directory -Force -Path $custom | Out-Null
    $nodes = @{
        "ComfyUI-Manager"              = "https://github.com/ltdrdata/ComfyUI-Manager.git"
        "ComfyUI-AnimateDiff-Evolved"  = "https://github.com/Kosinkadink/ComfyUI-AnimateDiff-Evolved.git"
        "ComfyUI-VideoHelperSuite"     = "https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git"
    }
    foreach ($name in $nodes.Keys) {
        $dest = Join-Path $custom $name
        if (-not (Test-Path $dest)) {
            Write-Host "Cloning $name ..."
            git clone --depth 1 $nodes[$name] $dest
        }
    }

    $wfSrc = Join-Path (Split-Path -Parent $PSScriptRoot) "workflows"
    $wfDest = Join-Path $sidecar "user\default\workflows"
    New-Item -ItemType Directory -Force -Path $wfDest | Out-Null
    if (Test-Path $wfSrc) {
        Copy-Item (Join-Path $wfSrc "amd_*.json") $wfDest -Force
        Write-Host "Copied Film Lab workflows → $wfDest"
    }

    $ckptDir = Join-Path $sidecar "models\checkpoints"
    $adDir = Join-Path $sidecar "models\animatediff_models"
    New-Item -ItemType Directory -Force -Path $ckptDir, $adDir | Out-Null

    $sd15 = "https://huggingface.co/stable-diffusion-v1-5/stable-diffusion-v1-5/resolve/main/v1-5-pruned-emaonly.safetensors"
    $motion = "https://huggingface.co/guoyww/animatediff/resolve/main/v3_sd15_mm.ckpt"
    $ltx = "https://huggingface.co/Lightricks/LTX-Video/resolve/main/ltxv-2b-0.9.8-distilled.safetensors"

    if ($DownloadModels) {
        Write-Host "Downloading open models (several GB). This is optional; you can copy files yourself."
        $sdPath = Join-Path $ckptDir "v1-5-pruned-emaonly.safetensors"
        $mmPath = Join-Path $adDir "v3_sd15_mm.ckpt"
        if (-not (Test-Path $sdPath)) {
            Write-Host "SD 1.5 emaonly → $sdPath"
            Invoke-WebRequest -Uri $sd15 -OutFile $sdPath
        }
        if (-not (Test-Path $mmPath)) {
            Write-Host "AnimateDiff v3 motion → $mmPath"
            Invoke-WebRequest -Uri $motion -OutFile $mmPath
        }
        Write-Host "Optional LTX 2B distilled (newer img2vid, still 6GB-tight):"
        Write-Host "  $ltx"
    } else {
        Write-Host ""
        Write-Host "Download these OPEN models into ComfyUI (or re-run with -DownloadModels):" -ForegroundColor Green
        Write-Host "  SD 1.5:  $sd15"
        Write-Host "    → $ckptDir\v1-5-pruned-emaonly.safetensors"
        Write-Host "  Motion:  $motion"
        Write-Host "    → $adDir\v3_sd15_mm.ckpt"
        Write-Host "  Optional LTX 2B distilled (stock ComfyUI LTXVImgToVideo):"
        Write-Host "    $ltx"
        Write-Host "    → $ckptDir\ltxv-2b-0.9.8-distilled.safetensors"
    }
} finally {
    Pop-Location
}

Write-Host ""
Write-Host "Done. Start the sidecar (leave it running):" -ForegroundColor Green
Write-Host "  powershell -ExecutionPolicy Bypass -File .\scripts\run_comfyui_amd.ps1"
Write-Host "Then in another PowerShell: .\scripts\run.ps1"
Write-Host "Shot desk → Generate MP4 (Local img2vid / AMD)"
Write-Host "First clip: 2–4s, 512x288. See docs\AMD_IMG2VID.md"
