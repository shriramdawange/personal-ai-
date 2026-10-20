import hmac
import os
from typing import Optional
from fastapi import FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, Field
from .config import settings
from .db import add_task, events, get_task, init_db, list_leads, list_tasks
from .orchestrator import Orchestrator
from .research import hunt_clients

app = FastAPI(title="AI Empire Engine API", version="0.2.0", description="Local control API for the AI business worker")
init_db()

class TaskInput(BaseModel):
    title: str = Field(min_length=3, max_length=180)
    description: str = Field(default="", max_length=12000)

class HuntInput(BaseModel):
    query: str = Field(min_length=3, max_length=400)
    limit: int = Field(default=5, ge=1, le=10)

def verify_access(authorization: Optional[str]):
    # Localhost mode can be used without a token. For any non-loopback bind,
    # EMPIRE_API_TOKEN is mandatory and requests must send a bearer token.
    host = os.getenv("EMPIRE_API_HOST", "127.0.0.1")
    token = os.getenv("EMPIRE_API_TOKEN", "").strip()
    if host not in ("127.0.0.1", "localhost", "::1"):
        if len(token) < 24:
            raise HTTPException(status_code=503, detail="Remote binding disabled: set a strong EMPIRE_API_TOKEN (24+ characters).")
        expected = "Bearer " + token
        if not authorization or not hmac.compare_digest(authorization, expected):
            raise HTTPException(status_code=401, detail="Valid bearer token required.")
    elif token and (not authorization or not hmac.compare_digest(authorization, "Bearer " + token)):
        raise HTTPException(status_code=401, detail="Valid bearer token required.")

@app.get("/health")
def health():
    return {"ok": True, "service": "ai-empire-engine", "model": settings.ollama_model, "mode": "local-runtime"}

@app.get("/tasks")
def tasks(limit: int = Query(default=50, ge=1, le=100), authorization: Optional[str] = Header(default=None)):
    verify_access(authorization)
    return {"items": list_tasks(limit)}

@app.post("/tasks", status_code=201)
def create_task(payload: TaskInput, authorization: Optional[str] = Header(default=None)):
    verify_access(authorization)
    task_id = add_task(payload.title.strip(), payload.description.strip())
    return get_task(task_id)

@app.get("/tasks/{task_id}")
def task_detail(task_id: int, authorization: Optional[str] = Header(default=None)):
    verify_access(authorization)
    item = get_task(task_id)
    if not item: raise HTTPException(status_code=404, detail="Task not found")
    return {"task": item, "events": events(task_id)}

@app.post("/tasks/{task_id}/run")
def run_task(task_id: int, authorization: Optional[str] = Header(default=None)):
    verify_access(authorization)
    if not get_task(task_id): raise HTTPException(status_code=404, detail="Task not found")
    try:
        return Orchestrator().run_task(task_id)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Task execution failed: {str(exc)[:500]}") from exc

@app.get("/leads")
def leads(limit: int = Query(default=50, ge=1, le=100), authorization: Optional[str] = Header(default=None)):
    verify_access(authorization)
    return {"items": list_leads(limit)}

@app.post("/leads/hunt")
def hunt(payload: HuntInput, authorization: Optional[str] = Header(default=None)):
    verify_access(authorization)
    try:
        return {"items": hunt_clients(payload.query, payload.limit)}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Lead search failed: {str(exc)[:500]}") from exc
