$ErrorActionPreference = "Stop"
$engine = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $engine
$python = Join-Path $engine ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Environment missing. Run .\setup.ps1 first." }
if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) { throw "Ollama is not installed." }

$api = $null
$worker = $null
try {
  $api = Start-Process -FilePath $python -ArgumentList @("-m","uvicorn","empire.api:app","--host","127.0.0.1","--port","8000") -WorkingDirectory $engine -PassThru -WindowStyle Hidden
  Write-Host "Local API started at http://127.0.0.1:8000 (PID $($api.Id))" -ForegroundColor Green

  # Keep the dedicated worker responsible for task execution and heartbeats.
  $worker = Start-Process -FilePath $python -ArgumentList @("-m","empire.cli","worker") -WorkingDirectory $engine -PassThru -WindowStyle Hidden
  Write-Host "Task worker started (PID $($worker.Id)); worker heartbeat is enabled." -ForegroundColor Green
  Write-Host "Starting recurring public-lead discovery in this terminal. Press Ctrl+C to stop all services."
  & $python -m empire.cli autopilot --interval-hours 24 --discover-only
} finally {
  if ($worker -and -not $worker.HasExited) {
    Stop-Process -Id $worker.Id -ErrorAction SilentlyContinue
  }
  if ($api -and -not $api.HasExited) {
    Stop-Process -Id $api.Id -ErrorAction SilentlyContinue
  }
}
