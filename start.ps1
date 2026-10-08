# Start AI Code Classroom: Docker Desktop, Ollama, backend (:8100), frontend (:5180), then open the browser.
# Anything already running is left as is, so it is safe to run this more than once.
# Usage: .\start.ps1 [-NoBrowser]   (or double-click start.cmd)

param([switch]$NoBrowser)

$ErrorActionPreference = 'Stop'
$root     = $PSScriptRoot
$backend  = Join-Path $root 'backend'
$frontend = Join-Path $root 'frontend'
$appUrl   = 'http://localhost:5180'

function Step($msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }
function Ok($msg)   { Write-Host "    $msg" -ForegroundColor Green }
function Warn($msg) { Write-Host "    $msg" -ForegroundColor Yellow }

function Test-Url($url) {
    try { Invoke-WebRequest $url -UseBasicParsing -TimeoutSec 2 | Out-Null; return $true } catch { return $false }
}

function Wait-Until([scriptblock]$check, [int]$seconds, [string]$what) {
    for ($i = 0; $i -lt $seconds; $i++) {
        if (& $check) { return $true }
        Start-Sleep 1
    }
    Warn "$what did not become ready within $seconds s."
    return $false
}

function Test-Port($port) {
    [bool](Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue)
}

function Test-Docker {
    $old = $ErrorActionPreference; $ErrorActionPreference = 'SilentlyContinue'
    docker info *> $null
    $ok = ($LASTEXITCODE -eq 0)
    $ErrorActionPreference = $old
    return $ok
}

# ─── 1. Docker Desktop (code grading sandbox) ────────────────────────────────
Step 'Docker Desktop'
if (Test-Docker) {
    Ok 'already running'
} else {
    $dockerExe = @(
        "$env:LOCALAPPDATA\Programs\DockerDesktop\Docker Desktop.exe",
        "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe"
    ) | Where-Object { Test-Path $_ } | Select-Object -First 1
    if (-not $dockerExe) {
        Warn 'Docker Desktop not found. Install it, or start it yourself; code submissions will fail without it.'
    } else {
        Start-Process $dockerExe
        Write-Host '    starting (this can take a minute)...'
        if (Wait-Until { Test-Docker } 180 'Docker') { Ok 'running' }
    }
}

if (Test-Docker) {
    $old = $ErrorActionPreference; $ErrorActionPreference = 'SilentlyContinue'
    $image = docker images -q python-runner
    $ErrorActionPreference = $old
    if ($image) {
        Ok 'python-runner image present'
    } else {
        Write-Host '    building python-runner image (first run only)...'
        docker build -t python-runner (Join-Path $backend 'docker\python_runner')
        Ok 'python-runner image built'
    }
}

# ─── 2. Ollama (AI Generator & AI Tutor) ──────────────────────────────────────
Step 'Ollama'
if (Test-Url 'http://127.0.0.1:11434/api/tags') {
    Ok 'already running'
} else {
    $ollamaApp = "$env:LOCALAPPDATA\Programs\Ollama\ollama app.exe"
    $ollamaCli = "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe"
    if (Test-Path $ollamaApp) { Start-Process $ollamaApp }
    elseif (Test-Path $ollamaCli) { Start-Process $ollamaCli -ArgumentList 'serve' -WindowStyle Minimized }
    else { Warn 'Ollama not found. AI features will not work until it is installed and running.' }
    if (Wait-Until { Test-Url 'http://127.0.0.1:11434/api/tags' } 60 'Ollama') { Ok 'running' }
}

# ─── 3. Backend (:8100) ───────────────────────────────────────────────────────
Step 'Backend (port 8100)'
if (Test-Port 8100) {
    Ok 'already running'
} else {
    Start-Process powershell -WorkingDirectory $backend -ArgumentList @(
        '-NoExit', '-ExecutionPolicy', 'Bypass', '-Command',
        "`$host.UI.RawUI.WindowTitle='AI Code Classroom - backend :8100'; .\run.ps1"
    )
    if (Wait-Until { Test-Url 'http://127.0.0.1:8100/health' } 60 'Backend') { Ok 'running' }
}

# ─── 4. Frontend (:5180) ──────────────────────────────────────────────────────
Step 'Frontend (port 5180)'
if (Test-Port 5180) {
    Ok 'already running'
} else {
    if (-not (Test-Path (Join-Path $frontend 'node_modules'))) {
        Write-Host '    installing npm packages (first run only)...'
        Push-Location $frontend; npm install; Pop-Location
    }
    Start-Process powershell -WorkingDirectory $frontend -ArgumentList @(
        '-NoExit', '-ExecutionPolicy', 'Bypass', '-Command',
        "`$host.UI.RawUI.WindowTitle='AI Code Classroom - frontend :5180'; npm run dev"
    )
    if (Wait-Until { Test-Url $appUrl } 60 'Frontend') { Ok 'running' }
}

# ─── 5. Open the app ──────────────────────────────────────────────────────────
if (-not $NoBrowser) {
    Step "Opening $appUrl"
    Start-Process $appUrl
}
Write-Host "`nAll set. Keep the two 'AI Code Classroom' windows open. Run .\stop.ps1 to stop the servers.`n" -ForegroundColor Green
