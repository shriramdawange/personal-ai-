# AI Empire Architecture

## Current implementation
Static HTML/CSS/JavaScript dashboard. Tasks are stored in browser localStorage. There is no server, model, authentication, multi-device sync, or real autonomous execution.

## Target architecture

```text
Phone / Browser
      |
      v
Dashboard UI
      |
      v
Task API + Durable Database
      |
      v
Orchestrator (state machine + limits)
      |
      +--> Research agent
      +--> Builder agent
      +--> Quality-check agent
      +--> Business-operator agent
      |
      v
Output verification + audit log
      |
      v
Human approval for external actions
```

## Suggested task lifecycle
`queued -> running -> needs_approval -> succeeded`
A task may instead transition to `failed` or return to `queued` after a bounded retry. Store timestamps and the reason for each transition.

## Implementation order
1. Add automated checks for the current front-end.
2. Add an API and durable storage with input validation and per-user access control.
3. Add a worker process with explicit task/step limits and audit events.
4. Integrate a model adapter behind a small interface; verify local disk, RAM, and model requirements before installation.
5. Connect selected specialist instructions from Agency Agents.
6. Add independent output checks and a human approval queue.
7. Consider free static hosting for the dashboard, while documenting that free hosting does not guarantee always-on compute.

## Operational safety
- Keep API keys out of Git and browser JavaScript.
- Never execute model-generated shell commands without review and a sandbox.
- Default external actions to disabled.
- Add a stop control and per-task resource limits before enabling autonomous loops.
