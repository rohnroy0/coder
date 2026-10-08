# Start the backend with the project's virtualenv on port 8100 (the frontend proxies /api here).
# Usage: .\run.ps1
#
# Auto-reload is done by `watchfiles` restarting the whole server process when a .py file under
# app/ changes. uvicorn's own --reload hangs on this Windows setup: it stops the old worker with a
# Ctrl+C event that never arrives, so the reload waits forever.
Set-Location $PSScriptRoot
& .\win_venv\Scripts\watchfiles.exe --filter python --target-type command `
    '.\win_venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8100' app
