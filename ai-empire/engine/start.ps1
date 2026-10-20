$ErrorActionPreference = "Stop"
$engine = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $engine
$python = Join-Path $engine ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Environment missing. Run .\setup.ps1 first." }
if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) { throw "Ollama is not installed." }

$api = Start-Process -FilePath $python -ArgumentList @("-m","uvicorn","empire.api:app","--host","127.0.0.1","--port","8000") -WorkingDirectory $engine -PassThru
Write-Host "Local API started at http://127.0.0.1:8000 (PID $($api.Id))"
Write-Host "Starting worker in this terminal. Press Ctrl+C to stop the worker."
try {
  & $python -m empire.cli autopilot --interval-hours 24
} finally {
  Stop-Process -Id $api.Id -ErrorAction SilentlyContinue
}
