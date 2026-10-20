$ErrorActionPreference = "Stop"
$engine = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $engine

Write-Host "AI Empire Engine setup" -ForegroundColor Cyan
if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
  throw "Python launcher (py) was not found. Install Python 3.10+ first."
}
if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
  throw "Ollama was not found. Install Ollama, then rerun this setup script."
}

# Reuse an existing model without demanding space for a second download.
$models = & ollama list
$modelReady = $models -match "qwen2.5-coder:3b"
$engineDrive = (Split-Path -Qualifier (Get-Location).Path).TrimEnd(':')
$engineFreeGB = [math]::Round((Get-Volume -DriveLetter $engineDrive).SizeRemaining / 1GB, 1)
Write-Host "Free space on engine drive ($engineDrive): $engineFreeGB GB"

if ($engineFreeGB -lt 2) {
  throw "STOP: At least 2 GB free is required on the engine drive for Python dependencies and the virtual environment."
}

$modelStore = if ($env:OLLAMA_MODELS) { $env:OLLAMA_MODELS } else { Join-Path $env:USERPROFILE ".ollama\models" }
$modelDrive = (Split-Path -Qualifier $modelStore).TrimEnd(':')
if (-not $modelReady) {
  $modelFreeGB = [math]::Round((Get-Volume -DriveLetter $modelDrive).SizeRemaining / 1GB, 1)
  Write-Host "Free space on Ollama model drive ($modelDrive): $modelFreeGB GB"
  if ($modelFreeGB -lt 15) {
    throw "STOP: qwen2.5-coder:3b is not installed and at least 15 GB free is recommended on the Ollama model drive. Free space or configure OLLAMA_MODELS to use a drive with sufficient space; no model will be downloaded."
  }
} else {
  Write-Host "Existing qwen2.5-coder:3b model found; reusing it." -ForegroundColor Green
}

if (-not (Test-Path ".venv")) { py -3 -m venv .venv }
& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt
if (-not (Test-Path ".env")) { Copy-Item ".env.example" ".env" }

if (-not $modelReady) {
  Write-Host "Pulling local model qwen2.5-coder:3b. This can take several GB." -ForegroundColor Yellow
  & ollama pull qwen2.5-coder:3b
}
& ".\.venv\Scripts\python.exe" -m empire.cli init
& ".\.venv\Scripts\python.exe" -m unittest discover -s tests -v
Write-Host "Setup complete. Use .\start.ps1 to start the local API and worker." -ForegroundColor Green
