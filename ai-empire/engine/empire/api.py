import hmac
import os
from typing import Optional
from fastapi import FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, Field
from .config import settings
from .db import (
    add_task, create_invoice, create_project, events, get_task, init_db,
    list_invoices, list_leads, list_projects, list_tasks,
    update_lead_status, update_project_status
)
from .orchestrator import Orchestrator
from .research import hunt_clients

app = FastAPI(title="AI Empire Engine API", version="0.3.0", description="Local control API for the AI business worker")
init_db()

class TaskInput(BaseModel):
    title: str = Field(min_length=3, max_length=180)
    description: str = Field(default="", max_length=12000)

class HuntInput(BaseModel):
    query: str = Field(min_length=3, max_length=400)
    limit: int = Field(default=5, ge=1, le=10)

class LeadStatusInput(BaseModel):
    status: str
    note: str = Field(default="", max_length=4000)

class ProjectInput(BaseModel):
    name: str = Field(min_length=2, max_length=300)
    scope: str = Field(default="", max_length=12000)
    lead_id: Optional[int] = Field(default=None, ge=1)
    budget_paise: int = Field(default=0, ge=0, le=100000000000)

class ProjectStatusInput(BaseModel):
    status: str

class InvoiceInput(BaseModel):
    project_id: int = Field(ge=1)
    description: str = Field(min_length=2, max_length=1000)
    amount_paise: int = Field(ge=0, le=100000000000)
    due_date: Optional[str] = Field(default=None, max_length=30)

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

@app.patch("/leads/{lead_id}/status")
def lead_status(lead_id: int, payload: LeadStatusInput, authorization: Optional[str] = Header(default=None)):
    verify_access(authorization)
    try:
        if not update_lead_status(lead_id, payload.status, payload.note):
            raise HTTPException(status_code=404, detail="Lead not found")
        return {"ok": True, "lead_id": lead_id, "status": payload.status}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

@app.get("/projects")
def projects(limit: int = Query(default=100, ge=1, le=200), authorization: Optional[str] = Header(default=None)):
    verify_access(authorization)
    return {"items": list_projects(limit)}

@app.post("/projects", status_code=201)
def project_create(payload: ProjectInput, authorization: Optional[str] = Header(default=None)):
    verify_access(authorization)
    project_id = create_project(payload.name.strip(), payload.scope.strip(), payload.lead_id, payload.budget_paise)
    return next(item for item in list_projects() if item["id"] == project_id)

@app.patch("/projects/{project_id}/status")
def project_status(project_id: int, payload: ProjectStatusInput, authorization: Optional[str] = Header(default=None)):
    verify_access(authorization)
    try:
        if not update_project_status(project_id, payload.status):
            raise HTTPException(status_code=404, detail="Project not found")
        return {"ok": True, "project_id": project_id, "status": payload.status}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

@app.get("/invoices")
def invoices(limit: int = Query(default=100, ge=1, le=200), authorization: Optional[str] = Header(default=None)):
    verify_access(authorization)
    return {"items": list_invoices(limit)}

@app.post("/invoices", status_code=201)
def invoice_create(payload: InvoiceInput, authorization: Optional[str] = Header(default=None)):
    verify_access(authorization)
    try:
        invoice_id = create_invoice(payload.project_id, payload.description.strip(), payload.amount_paise, payload.due_date)
        if invoice_id is None:
            raise HTTPException(status_code=404, detail="Project not found")
        return next(item for item in list_invoices() if item["id"] == invoice_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
