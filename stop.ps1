# Stop the AI Code Classroom backend (:8100) and frontend (:5180).
# Docker Desktop and Ollama are left running (other apps may use them).
# Usage: .\stop.ps1

# 1. Close the server windows opened by start.ps1 and the backend's auto-reload watcher first,
#    so nothing restarts the servers while they are being stopped.
Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" |
    Where-Object { $_.CommandLine -match 'AI Code Classroom - (backend|frontend)' } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Get-CimInstance Win32_Process |
    Where-Object { $_.CommandLine -match 'watchfiles' -and $_.CommandLine -match 'port 8100' } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }

# 2. Stop whatever is still listening on the two ports.
foreach ($port in 8100, 5180) {
    $conns = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    foreach ($c in $conns) { Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue }
}
Start-Sleep 1

foreach ($port in 8100, 5180) {
    if (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue) {
        Write-Host "port $port : still in use" -ForegroundColor Yellow
    } else {
        Write-Host "port $port : stopped" -ForegroundColor Green
    }
}
