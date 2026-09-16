# Resolve a real CPython (not the Microsoft Store stub).
# ComfyUI + torch-directml want 3.11 or 3.12. Film Lab can use 3.11–3.14.

function Get-FilmLabPython {
    param([switch]$Prefer312)
    $candidates = @(
        @{ Cmd = "py"; Args = @("-3.12") },
        @{ Cmd = "py"; Args = @("-3.11") },
        @{ Cmd = "py"; Args = @("-3") },
        @{ Cmd = "python"; Args = @() }
    )
    if (-not $Prefer312) {
        $candidates = @(
            @{ Cmd = "py"; Args = @("-3") },
            @{ Cmd = "py"; Args = @("-3.12") },
            @{ Cmd = "py"; Args = @("-3.11") },
            @{ Cmd = "python"; Args = @() }
        )
    }
    foreach ($c in $candidates) {
        if (-not (Get-Command $c.Cmd -ErrorAction SilentlyContinue)) { continue }
        try {
            $code = "import sys; print(sys.version_info.major); print(sys.version_info.minor); print(sys.executable)"
            $out = & $c.Cmd @($c.Args + @("-c", $code)) 2>$null
            if (-not $out) { continue }
            $lines = @($out)
            if ($lines.Count -lt 3) { continue }
            $major = [int]$lines[0]
            $minor = [int]$lines[1]
            $exe = [string]$lines[2]
            if ($exe -match "WindowsApps") { continue }
            if ($major -lt 3 -or $minor -lt 11) { continue }
            return [pscustomobject]@{
                Cmd     = $c.Cmd
                Args    = $c.Args
                Version = "$major.$minor"
                Exe     = $exe
            }
        } catch {
            continue
        }
    }
    return $null
}

function Invoke-FilmLabPython {
    param(
        [Parameter(Mandatory = $true)]$Python,
        [Parameter(Mandatory = $true)][string[]]$Arguments
    )
    & $Python.Cmd @($Python.Args + $Arguments)
}
