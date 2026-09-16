# Pin Film Lab to the Windows Desktop. Double-click — no folder hunting.
$ErrorActionPreference = "Stop"
. "$PSScriptRoot\_common.ps1"

$root = Get-FilmLabRoot
$start = Join-Path $root "START_FILM_LAB.bat"
$icon = Join-Path $root "assets\film_lab.ico"
$desktop = [Environment]::GetFolderPath("Desktop")
$lnk = Join-Path $desktop "Film Lab.lnk"

if (-not (Test-Path $start)) {
    Write-Error "START_FILM_LAB.bat missing at $start"
}

$w = New-Object -ComObject WScript.Shell
$sc = $w.CreateShortcut($lnk)
$sc.TargetPath = $start
$sc.WorkingDirectory = $root
$sc.WindowStyle = 1
$sc.Description = "Film Lab — offline-first local studio (Comfy GPU1 + desk)"
if (Test-Path $icon) { $sc.IconLocation = "$icon,0" }
$sc.Save()

Write-Host "Desktop shortcut: $lnk" -ForegroundColor Green
Write-Host "Double-click Film Lab. Works offline for local generation."
Write-Host "Repair: $root\REPAIR.bat"
