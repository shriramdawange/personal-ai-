$ErrorActionPreference = "Stop"
$engine = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $engine

Write-Host "AI Empire Engine setup" -ForegroundColor Cyan
$drive = Get-PSDrive -Name (Get-Location).Drive.Name
$freeGB = [math]::Round((Get-Volume -DriveLetter $drive.Name).SizeRemaining / 1GB, 1)
Write-Host "Free space on current drive: $freeGB GB"

if ($freeGB -lt 15) {
  Write-Host "STOP: At least 15 GB free is recommended before installing a local model. Free space first; no model will be downloaded." -ForegroundColor Yellow
  exit 2
}

if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
  throw "Python launcher (py) was not found. Install Python 3.10+ first."
}
if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
  throw "Ollama was not found. Install Ollama, then rerun this setup script."
}

if (-not (Test-Path ".venv")) { py -3 -m venv .venv }
& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt
if (-not (Test-Path ".env")) { Copy-Item ".env.example" ".env" }

$models = & ollama list
if ($models -notmatch "qwen2.5-coder:3b") {
  Write-Host "Pulling local model qwen2.5-coder:3b. This can take several GB." -ForegroundColor Yellow
  & ollama pull qwen2.5-coder:3b
}
& ".\.venv\Scripts\python.exe" -m empire.cli init
& ".\.venv\Scripts\python.exe" -m unittest discover -s tests -v
Write-Host "Setup complete. Use .\start.ps1 to start the local API and worker." -ForegroundColor Green
