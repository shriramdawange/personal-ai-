# AI Empire — Foundation

A mobile-friendly, zero-budget-first control panel prototype for a future AI-assisted business operating system.

## Current status

This is a **front-end prototype**, not an autonomous business yet.

### Working now
- Responsive dashboard
- Create tasks and mark them complete
- Tasks persist in this browser using localStorage
- Task status and counts update immediately
- Clear safety boundary: planned workers are not represented as running agents

### Not connected yet
- No language model is connected
- No real agent execution, backend, authentication, cloud database, or background worker
- Tasks are local to the current browser/device and are not synced to another device
- No emails, posts, purchases, deployments, or other external actions are executed

## Open the prototype

Open `index.html` in a browser or serve this folder as static files. No package installation or build command is needed.

## Planned architecture

1. **Control panel** — create and review work.
2. **Task API and durable storage** — validate tasks, persist status, and record audit events.
3. **Agent catalog** — adapt selected specialist instructions from [Agency Agents](https://github.com/msitarzewski/agency-agents), preserving the MIT license notice.
4. **Worker runtime** — connect a model only after hardware and disk space are checked.
5. **Orchestrator** — plan, execute bounded steps, retry safely, and verify outputs.
6. **Approval gates** — require human approval for external or destructive actions.
7. **Observability** — logs, cost limits, errors, and task history.

## Zero-budget constraints

- Prefer free and local tools; never assume free tiers are unlimited or permanent.
- Do not add secrets or API keys to this repository.
- Do not claim 24/7 operation from a local worker: it runs only while the computer and process are available.
- Keep human approval for spending money, contacting people, publishing, changing accounts, or deleting data.

## Next milestone

Add a tested task API and persistence layer before connecting a model. Avoid installing large local models until available disk space is checked.
