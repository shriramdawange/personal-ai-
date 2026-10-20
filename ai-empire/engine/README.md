# AI Empire Engine — Local AI Team Runtime

This is the **first real runtime layer**, not just a dashboard. It includes a persistent SQLite queue, a local Ollama model adapter, CEO planning, a specialist delivery step, independent QA review, bounded revision, artifact output, an audit trail, and best-effort public-web lead discovery with outreach drafts.

## Honest current scope

- **Working design implemented in code:** CLI, SQLite persistence, local Ollama calls, task lifecycle, research adapter, lead qualification, output artifacts, and audit events.
- **Not yet verified end-to-end:** the runtime has not been installed or executed on a target machine. No tests have been run against a live Ollama model or web search endpoint.
- **Not included:** sending emails, messaging prospects, making purchases, accepting contracts, charging clients, or deploying client code automatically. The engine prepares lead assessments and outreach drafts; external actions need explicit approval.
- **Not 24/7 by itself:** this worker runs only while the host computer and process are running. Free static hosting does not provide a dependable always-on worker.

## Requirements

- Python 3.10+
- Ollama installed and running
- A model pulled into Ollama; default is `qwen2.5-coder:3b`
- Internet access for public web lead discovery

This first version uses a local model and has no paid API requirement. Model performance and RAM requirements depend on the chosen model. On an 8 GB RAM laptop, a 3B quantized model may still be slow; ensure adequate disk space before installing it.

## Setup (Windows PowerShell)

The repository includes a guarded setup script. It reuses an already-installed model; before downloading a missing model, it checks the actual Ollama model-storage drive and refuses the download if less than 15 GB is free. It also requires at least 2 GB free on the engine drive for the Python environment and dependencies.

```powershell
cd ai-empire\engine
.\setup.ps1
```

Manual setup, if preferred:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
ollama pull qwen2.5-coder:3b
python -m empire.cli init
```

If Ollama is not on PATH, install/start it first. Do not run the model download until there is sufficient free disk space.

## Start the control interface

After setup completes, run the local API and worker:

```powershell
.\start.ps1
```

Then open `http://127.0.0.1:8000/` in a browser. The functional interface calls this engine's API to create/run tasks, hunt and review leads, manage project statuses, and create draft invoice records. `/system/status` reports API, database, Ollama reachability, and whether the configured model is installed. `/docs` provides interactive API documentation.

The UI is served by FastAPI from the same origin; no separate frontend build or paid hosting is required. Keep the server local. Do not expose it to the public internet without a reviewed authentication and TLS deployment.

## Use the team

```powershell
# Queue work
python -m empire.cli add-task "Create a landing page plan" --description "For a local bookkeeping firm; include sections and acceptance criteria."

# Run one queued task through CEO -> specialist -> QA
python -m empire.cli worker --once

# Or keep polling the queue while this computer is running
python -m empire.cli worker

# Discover possible leads; results are unverified and outreach is only drafted
python -m empire.cli hunt-clients --query "small business needs website redesign India"
python -m empire.cli leads

# Run one automatic lead-discovery cycle and process one queued task
python -m empire.cli autopilot --once

# Keep discovering leads and processing tasks daily while the computer stays on
python -m empire.cli autopilot --interval-hours 24

# Inspect task state and audit events
python -m empire.cli tasks
python -m empire.cli events 1
```

## How it works

1. Tasks are stored in `data/empire.db` and can be submitted through the CLI or local API.
2. CEO agent creates a plan and acceptance checks.
3. A specialist drafts the deliverable using the local model.
4. QA reviews the draft and may request one bounded revision.
5. Output and QA notes are saved under `workspace/`; explicit `FILE: path` fenced blocks are materialized into a task-isolated artifacts directory. Python syntax and JavaScript syntax (when Node is installed) receive static checks; this is not a substitute for full tests.
6. Leads can move through a CRM status pipeline, projects can be tracked through delivery states, and draft invoice records can be attached to projects. These records do not send outreach, sign contracts, deploy software, or process payments.
6. Client-hunting searches public results, asks the model to score fit using only supplied evidence, and saves a draft. Verify every prospect manually before outreach.

## API surface

- `GET /health` — basic service health
- `GET /system/status` — database and local model readiness
- `GET /tasks`, `POST /tasks`, `GET /tasks/{id}`, `POST /tasks/{id}/run`
- `GET /leads`, `POST /leads/hunt`, `PATCH /leads/{id}/status`
- `GET /projects`, `POST /projects`, `PATCH /projects/{id}/status`
- `GET /invoices`, `POST /invoices`

Task claiming uses a conditional database update to prevent the API and worker from claiming the same queued task concurrently. Automated tests cover this guard, dashboard serving, model readiness reporting, database lifecycle and existing artifact/research checks.

## Guardrails and limitations

- Model output is untrusted. The runtime does not execute model-generated shell commands.
- Never put API keys, passwords, or customer secrets in task descriptions.
- Public search results may be stale, blocked, duplicated, or misleading; validate leads before contacting them.
- Do not scrape behind logins or ignore a site's terms/rate limits.
- The local worker cannot operate when the computer is asleep or offline.
- There is no automatic mail sender. Outreach, publishing, purchases, contract acceptance, and other external actions remain approval-gated.
- SQLite is intended for a single-machine prototype, not concurrent multi-user production.

## Next engineering milestones

1. Run syntax checks and end-to-end tests on a machine with Python + Ollama.
2. Add retries, per-task timeouts, stronger parsing and deterministic QA gates.
3. Add a durable remote queue and authenticated control API if a cloud dashboard is needed.
4. Add CRM adapters and approval-gated outreach after validating the lead research quality.
5. Add sandboxed coding tools and test execution; never let the model run unrestricted shell commands.
6. Add monitoring, budget/rate limits, backup, and recovery before enabling long-running autonomy.
