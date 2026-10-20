import ast
import re
import shutil
import subprocess
from pathlib import Path
from .config import settings

FILE_HEADER = re.compile(r"^FILE:\s+([^\n]+)\n", re.MULTILINE)
FENCED_BLOCK = re.compile(r"^FILE:\s+([^\n]+)\n\s*```[^\n]*\n(.*?)\n```", re.MULTILINE | re.DOTALL)

def _safe_relative_path(raw: str) -> Path:
    cleaned = raw.strip().strip("`'\"")
    rel = Path(cleaned)
    if rel.is_absolute() or not rel.parts or any(part in ("..", "") for part in rel.parts):
        raise ValueError(f"Unsafe artifact path rejected: {raw}")
    return rel

def materialize_files(task_id: int, output: str):
    """Write only explicitly marked FILE: fenced blocks under this task's workspace."""
    matches = list(FENCED_BLOCK.finditer(output))
    if not matches:
        return {"files": [], "message": "No FILE: path + fenced code blocks were found; full deliverable is saved as Markdown."}
    root = (settings.workspace / f"task-{task_id}" / "artifacts").resolve()
    root.mkdir(parents=True, exist_ok=True)
    written=[]
    for match in matches:
        rel = _safe_relative_path(match.group(1))
        target = (root / rel).resolve()
        if root not in target.parents and target != root:
            raise ValueError("Artifact path escaped task workspace")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(match.group(2) + "\n", encoding="utf-8")
        written.append(str(target))
    return {"files": written, "message": f"Wrote {len(written)} artifact file(s) to isolated task workspace."}

def validate_artifacts(paths):
    results=[]
    for raw in paths:
        path=Path(raw)
        suffix=path.suffix.lower()
        if suffix == ".py":
            try:
                ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
                results.append({"file":str(path),"check":"python-ast","status":"pass"})
            except (SyntaxError, UnicodeDecodeError) as exc:
                results.append({"file":str(path),"check":"python-ast","status":"fail","detail":str(exc)})
        elif suffix in (".js", ".mjs", ".cjs") and shutil.which("node"):
            try:
                proc=subprocess.run(["node","--check",str(path)],capture_output=True,text=True,timeout=8,check=False)
                results.append({"file":str(path),"check":"node-syntax","status":"pass" if proc.returncode==0 else "fail","detail":(proc.stderr or proc.stdout)[:1000]})
            except (subprocess.TimeoutExpired, OSError) as exc:
                results.append({"file":str(path),"check":"node-syntax","status":"error","detail":str(exc)})
        else:
            results.append({"file":str(path),"check":"file-presence-only","status":"not_run","detail":"No syntax checker configured for this file type."})
    return results
