param(
  [string]$BaseUrl = "http://127.0.0.1:8000",
  [int]$TimeoutMinutes = 30
)

$ErrorActionPreference = "Stop"
$BaseUrl = $BaseUrl.TrimEnd("/")
$deadline = (Get-Date).AddMinutes([math]::Max(1, $TimeoutMinutes))

Write-Host "AI Empire live end-to-end verification" -ForegroundColor Cyan
Write-Host "API: $BaseUrl"

$health = Invoke-RestMethod -Uri "$BaseUrl/health" -TimeoutSec 10
if (-not $health.ok) { throw "API health check failed." }
Write-Host "[PASS] API is responding." -ForegroundColor Green

$status = Invoke-RestMethod -Uri "$BaseUrl/system/status" -TimeoutSec 10
if (-not $status.database.ok) { throw "SQLite database is not ready." }
if (-not $status.ollama.reachable) { throw "Ollama is not reachable. Start Ollama and retry." }
if (-not $status.ollama.model_available) {
  throw "Configured model '$($status.ollama.model)' is not installed. Check Ollama and available disk space."
}
if (-not $status.worker.alive_recently) {
  throw "Worker heartbeat is not fresh. Start the system with .\start.ps1 and retry."
}
Write-Host "[PASS] Database, Ollama model, and worker heartbeat are ready." -ForegroundColor Green

$model = Invoke-RestMethod -Method Post -Uri "$BaseUrl/system/model-test" -ContentType "application/json" -Body "{}" -TimeoutSec 300
if (-not $model.ok) { throw "Live model inference check failed: $($model.response)" }
Write-Host "[PASS] Live inference succeeded with $($model.model)." -ForegroundColor Green

$payload = @{
  title = "AI Empire live smoke test"
  description = "Create a concise smoke-test deliverable with three bullets: system purpose, the importance of QA, and a safe next step. Do not invent business results or claim external actions were performed."
} | ConvertTo-Json -Depth 5
$task = Invoke-RestMethod -Method Post -Uri "$BaseUrl/tasks" -ContentType "application/json" -Body $payload -TimeoutSec 15
$taskId = [int]$task.id
Write-Host "Queued end-to-end task #$taskId. Waiting for the dedicated worker..."

$finished = $false
while ((Get-Date) -lt $deadline) {
  Start-Sleep -Seconds 5
  $detail = Invoke-RestMethod -Uri "$BaseUrl/tasks/$taskId" -TimeoutSec 15
  $taskState = $detail.task.status
  Write-Host "  Task #$taskId status: $taskState"
  if ($taskState -in @("succeeded", "needs_review", "failed")) {
    $finished = $true
    break
  }
}
if (-not $finished) {
  throw "Task #$taskId did not finish within $TimeoutMinutes minute(s). Inspect the worker heartbeat and task events."
}
if ($taskState -eq "failed") {
  throw "Task #$taskId failed: $($detail.task.error). Inspect /tasks/$taskId for its event trail."
}
if (-not $detail.task.result_path) {
  throw "Task #$taskId finished without a saved report."
}

$artifactPath = Join-Path $env:TEMP "ai-empire-smoke-test-$taskId.md"
Invoke-WebRequest -Uri "$BaseUrl/tasks/$taskId/artifact" -OutFile $artifactPath -TimeoutSec 20
$report = Get-Content -LiteralPath $artifactPath -Raw
if ($report -notmatch "## CEO plan" -or $report -notmatch "## QA review") {
  throw "Saved report is missing expected orchestration sections: $artifactPath"
}
Write-Host "[PASS] Worker completed the task and the report passed artifact checks." -ForegroundColor Green
Write-Host "Task: #$taskId ($taskState)"
Write-Host "Report: $artifactPath"
Write-Host "Event trail: $BaseUrl/tasks/$taskId"

if ($taskState -eq "needs_review") {
  Write-Warning "The pipeline ran, but QA/static checks requested human review. Inspect the saved report before treating the deliverable as accepted."
} else {
  Write-Host "END-TO-END CHECK PASSED." -ForegroundColor Green
}
