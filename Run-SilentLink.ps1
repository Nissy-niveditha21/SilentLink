<#
.SYNOPSIS
    Launch SilentLink from PowerShell on Windows.

.DESCRIPTION
    1. Ensures a Python virtual environment exists at .\veenv (creates it if missing).
    2. Installs requirements.txt inside the venv on first run or when --upgrade is passed.
    3. Copies .env.example → .env if .env is missing so the app boots without hand-editing.
    4. Launches `python run.py` with any extra arguments you provide.

.PARAMETER Host
    Override the bind host (default: whatever settings.HOST says, usually 127.0.0.1).

.PARAMETER Port
    Override the bind port (default: whatever settings.PORT says, usually 8000).

.PARAMETER NoReload
    Disable uvicorn auto-reload (useful for production / shared dev boxes).

.PARAMETER Upgrade
    Re-run `pip install -r requirements.txt` inside the venv before starting.

.PARAMETER NewWindow
    Open the backend in a new PowerShell window instead of blocking the current one.

.EXAMPLE
    .\Run-SilentLink.ps1
    .\Run-SilentLink.ps1 -Port 9000
    .\Run-SilentLink.ps1 -Host 0.0.0.0 -NoReload -Upgrade
#>

[CmdletBinding()]
param(
    [string]$Host,
    [int]$Port,
    [switch]$NoReload,
    [switch]$Upgrade,
    [switch]$NewWindow
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $Root
try {
    if (-not (Test-Path ".env")) {
        if (Test-Path ".env.example") {
            Write-Host "[SilentLink] .env missing — copying .env.example → .env" -ForegroundColor Cyan
            Copy-Item ".env.example" ".env"
        } else {
            Write-Warning "[SilentLink] .env and .env.example both missing. Runtime will use ephemeral SECRET_KEY."
        }
    }

    $VenvDir = Join-Path $Root "veenv"
    $PythonExe = Join-Path $VenvDir "Scripts\python.exe"
    if (-not (Test-Path $PythonExe)) {
        Write-Host "[SilentLink] Creating virtual environment at veenv\ ..." -ForegroundColor Cyan
        $sysPy = Get-Command python.exe -ErrorAction SilentlyContinue
        if (-not $sysPy) { $sysPy = Get-Command py.exe -ErrorAction SilentlyContinue }
        if (-not $sysPy) {
            throw "No python.exe or py.exe on PATH. Install Python 3.10+ from python.org then re-run."
        }
        & $sysPy.Source -m venv $VenvDir
        if ($LASTEXITCODE -ne 0) { throw "venv creation failed (exit=$LASTEXITCODE)" }
        $Upgrade = $true
    }

    if ($Upgrade -or -not (Test-Path (Join-Path $VenvDir "Scripts\uvicorn.exe"))) {
        Write-Host "[SilentLink] Installing requirements.txt into veenv\ ..." -ForegroundColor Cyan
        & $PythonExe -m pip install --upgrade pip | Out-Null
        & $PythonExe -m pip install -r requirements.txt
        if ($LASTEXITCODE -ne 0) { throw "pip install failed (exit=$LASTEXITCODE)" }
    }

    $argv = @()
    if ($PSBoundParameters.ContainsKey('Host'))   { $argv += @("--host", $Host) }
    if ($PSBoundParameters.ContainsKey('Port'))   { $argv += @("--port", $Port.ToString()) }
    if ($NoReload)                                { $argv += "--no-reload" }

    $CmdLine = "& `"$PythonExe`" `"$(Join-Path $Root run.py)`" $($argv -join ' ')"

    Write-Host ""
    Write-Host "  ███████╗██╗██╗     ███████╗███╗   ██╗████████╗██╗     ██╗███╗   ██╗██╗  ██╗" -ForegroundColor Magenta
    Write-Host "  ██╔════╝██║██║     ██╔════╝████╗  ██║╚══██╔══╝██║     ██║████╗  ██║██║ ██╔╝" -ForegroundColor Magenta
    Write-Host "  ███████╗██║██║     █████╗  ██╔██╗ ██║   ██║   ██║     ██║██╔██╗ ██║█████╔╝ " -ForegroundColor Magenta
    Write-Host "  ╚════██║██║██║     ██╔══╝  ██║╚██╗██║   ██║   ██║     ██║██║╚██╗██║██╔═██╗ " -ForegroundColor Magenta
    Write-Host "  ███████║██║███████╗███████╗██║ ╚████║   ██║   ███████╗██║██║ ╚████║██║  ██╗" -ForegroundColor Magenta
    Write-Host "  ╚══════╝╚═╝╚══════╝╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝" -ForegroundColor Magenta
    Write-Host ""

    $launchUrl = "http://127.0.0.1:8000"
    if ($PSBoundParameters.ContainsKey('Port')) { $launchUrl = "http://127.0.0.1:$Port" }
    if ($PSBoundParameters.ContainsKey('Host') -and $Host -eq "0.0.0.0") { $launchUrl = "http://127.0.0.1:$($PSBoundParameters['Port'] ? $Port : 8000)" }
    Write-Host "[SilentLink] Opening browser at $launchUrl in 3s…" -ForegroundColor Green
    Start-Sleep -Seconds 3
    Start-Process $launchUrl

    if ($NewWindow) {
        Start-Process powershell.exe -ArgumentList @("-NoExit", "-Command", "Set-Location '$Root'; $CmdLine")
        Write-Host "[SilentLink] Server started in a new window. You can close this one." -ForegroundColor Green
    } else {
        Write-Host "[SilentLink] Running: $CmdLine" -ForegroundColor Green
        Write-Host "            Press Ctrl+C to stop the server.`n" -ForegroundColor DarkGray
        Invoke-Expression $CmdLine
    }
}
finally {
    Pop-Location
}
