from dataclasses import dataclass
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:3b")
    db_path: Path = Path(os.getenv("EMPIRE_DB_PATH", "./data/empire.db"))
    workspace: Path = Path(os.getenv("EMPIRE_WORKSPACE", "./workspace"))
    poll_seconds: int = max(3, int(os.getenv("EMPIRE_POLL_SECONDS", "15")))
    stale_task_minutes: int = max(5, int(os.getenv("EMPIRE_STALE_TASK_MINUTES", "60")))
    llm_timeout_seconds: int = max(15, int(os.getenv("EMPIRE_LLM_TIMEOUT_SECONDS", "180")))
    llm_retries: int = max(0, min(3, int(os.getenv("EMPIRE_LLM_RETRIES", "2"))))
    max_revisions: int = max(0, min(2, int(os.getenv("EMPIRE_MAX_REVISIONS", "1"))))
    business_name: str = os.getenv("BUSINESS_NAME", "Your AI Studio")
    business_services: str = os.getenv("BUSINESS_SERVICES", "websites, automation, AI prototypes, software development")
    portfolio_url: str = os.getenv("BUSINESS_PORTFOLIO_URL", "")
    contact_email: str = os.getenv("BUSINESS_CONTACT_EMAIL", "")
    lead_region: str = os.getenv("LEAD_SEARCH_REGION", "India")
    autopilot_queries: str = os.getenv("AUTOPILOT_QUERIES", "small business website redesign India|small business process automation India|SME AI automation services India")

settings = Settings()
