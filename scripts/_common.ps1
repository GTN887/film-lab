# Shared Film Lab desktop helpers. Works offline. No credits.

function Get-FilmLabRoot {
    return (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}

function Get-FilmLabLogsDir {
    $dir = Join-Path (Get-FilmLabRoot) "data\logs"
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    return $dir
}

function Write-FilmLabLog {
    param([string]$Message)
    $line = "{0} {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
    Add-Content -Path (Join-Path (Get-FilmLabLogsDir) "launcher.log") -Value $line
    Write-Host $line
}

function Get-FilmLabPort {
    param([int]$Default = 43123)
    if ($env:FILM_LAB_PORT) { return [int]$env:FILM_LAB_PORT }
    return $Default
}

function Get-ComfyPort {
    param([int]$Default = 8188)
    if ($env:FILM_LAB_COMFY_PORT) { return [int]$env:FILM_LAB_COMFY_PORT }
    return $Default
}

function Test-FilmLabPortOpen {
    param([int]$Port)
    try {
        $client = New-Object System.Net.Sockets.TcpClient
        $iar = $client.BeginConnect("127.0.0.1", $Port, $null, $null)
        $ok = $iar.AsyncWaitHandle.WaitOne(250, $false)
        if ($ok) { $client.EndConnect($iar) | Out-Null }
        $client.Close()
        return $ok
    } catch {
        return $false
    }
}

function Stop-FilmLabPort {
    param([int]$Port)
    $killed = 0
    try {
        $conns = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
        foreach ($c in $conns) {
            if ($c.OwningProcess) {
                Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue
                $killed++
            }
        }
    } catch {
        $lines = netstat -ano | Select-String ":$Port\s"
        foreach ($line in $lines) {
            $procId = ($line.ToString() -split "\s+")[-1]
            if ($procId -match "^\d+$") {
                Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
                $killed++
            }
        }
    }
    Write-FilmLabLog "Kill port $Port (stopped $killed process(es))."
}

function Start-FilmLabComfyWindow {
    $root = Get-FilmLabRoot
    $script = Join-Path $root "scripts\run_comfyui_amd.ps1"
    Start-Process -FilePath "powershell.exe" -WorkingDirectory $root -ArgumentList @(
        "-NoProfile", "-ExecutionPolicy", "Bypass", "-NoExit", "-File", $script
    )
    Write-FilmLabLog "Started Comfy window (GPU1 / cuda-device 1)."
}

function Start-FilmLabAppWindow {
    param([switch]$SafeMode)
    $root = Get-FilmLabRoot
    $script = Join-Path $root "scripts\run.ps1"
    $args = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-NoExit", "-File", $script)
    $envMap = @{
        FILM_LAB_PORT = "$(Get-FilmLabPort)"
        FILM_LAB_HOST = "127.0.0.1"
    }
    if ($SafeMode) { $envMap["FILM_LAB_SAFE_MODE"] = "1" }
    $psi = @{
        FilePath         = "powershell.exe"
        WorkingDirectory = $root
        ArgumentList     = $args
    }
    Start-Process @psi
    Write-FilmLabLog "Started Film Lab window$(if ($SafeMode) { ' (safe mode)' })."
}

function Wait-FilmLabPort {
    param([int]$Port, [int]$Seconds = 40)
    for ($i = 0; $i -lt $Seconds; $i++) {
        if (Test-FilmLabPortOpen -Port $Port) { return $true }
        Start-Sleep -Seconds 1
    }
    return $false
}
