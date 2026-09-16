# Film Lab Repair toolkit. Works offline. No internet required.
param(
    [ValidateSet("menu", "restart-lab", "restart-comfy", "kill-ports", "logs", "safe")]
    [string]$Action = "menu"
)
$ErrorActionPreference = "Stop"
. "$PSScriptRoot\_common.ps1"

function Show-Menu {
    Write-Host ""
    Write-Host "FILM LAB  —  Repair (offline)" -ForegroundColor Yellow
    Write-Host "Works offline for local generation."
    Write-Host ""
    Write-Host "  1  Restart Film Lab"
    Write-Host "  2  Restart Comfy (GPU1)"
    Write-Host "  3  Kill ports 43123 / 8188"
    Write-Host "  4  Open logs"
    Write-Host "  5  Safe mode (480p / short clip) then START"
    Write-Host "  Q  Quit"
    Write-Host ""
    $pick = Read-Host "Choose"
    switch ($pick) {
        "1" { Invoke-Repair "restart-lab" }
        "2" { Invoke-Repair "restart-comfy" }
        "3" { Invoke-Repair "kill-ports" }
        "4" { Invoke-Repair "logs" }
        "5" { Invoke-Repair "safe" }
        default { return }
    }
}

function Invoke-Repair {
    param([string]$Name)
    $root = Get-FilmLabRoot
    Set-Location $root
    switch ($Name) {
        "kill-ports" {
            Stop-FilmLabPort -Port (Get-FilmLabPort)
            Stop-FilmLabPort -Port (Get-ComfyPort)
            Write-Host "Ports cleared." -ForegroundColor Green
        }
        "restart-lab" {
            Stop-FilmLabPort -Port (Get-FilmLabPort)
            Start-Sleep -Seconds 1
            Start-FilmLabAppWindow
            if (Wait-FilmLabPort -Port (Get-FilmLabPort) -Seconds 40) {
                Start-Process "http://127.0.0.1:$(Get-FilmLabPort)"
            }
        }
        "restart-comfy" {
            Stop-FilmLabPort -Port (Get-ComfyPort)
            Start-Sleep -Seconds 1
            Start-FilmLabComfyWindow
        }
        "logs" {
            $dir = Get-FilmLabLogsDir
            Write-Host "Logs: $dir"
            Invoke-Item $dir
        }
        "safe" {
            $flag = Join-Path $root "data\safe_mode.flag"
            New-Item -ItemType Directory -Force -Path (Split-Path $flag) | Out-Null
            Set-Content -Path $flag -Value "480p / 5s`n"
            $env:FILM_LAB_SAFE_MODE = "1"
            Write-FilmLabLog "Safe mode on (480p / 5s)."
            Stop-FilmLabPort -Port (Get-FilmLabPort)
            Start-Sleep -Seconds 1
            Start-FilmLabAppWindow -SafeMode
            if (Wait-FilmLabPort -Port (Get-FilmLabPort) -Seconds 40) {
                Start-Process "http://127.0.0.1:$(Get-FilmLabPort)"
            }
        }
    }
}

if ($Action -eq "menu") {
    Show-Menu
} else {
    Invoke-Repair $Action
}
