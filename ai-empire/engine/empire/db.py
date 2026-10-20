import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from .config import settings

def now():
    return datetime.now(timezone.utc).isoformat()

def connect():
    settings.db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(settings.db_path, timeout=30)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    return con

def init_db():
    with connect() as con:
        con.executescript('''
        CREATE TABLE IF NOT EXISTS tasks(id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, description TEXT NOT NULL DEFAULT '', status TEXT NOT NULL DEFAULT 'queued', result_path TEXT, error TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY AUTOINCREMENT, task_id INTEGER, agent TEXT NOT NULL, event TEXT NOT NULL, detail TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS leads(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, url TEXT NOT NULL UNIQUE, snippet TEXT NOT NULL DEFAULT '', fit_score INTEGER NOT NULL DEFAULT 0, rationale TEXT NOT NULL DEFAULT '', outreach_draft TEXT NOT NULL DEFAULT '', status TEXT NOT NULL DEFAULT 'discovered', created_at TEXT NOT NULL);
        ''')

def add_task(title, description=''):
    stamp = now()
    with connect() as con:
        cur = con.execute('INSERT INTO tasks(title,description,status,created_at,updated_at) VALUES(?,?,\'queued\',?,?)', (title, description, stamp, stamp))
        return cur.lastrowid

def list_tasks(limit=30):
    with connect() as con:
        return [dict(r) for r in con.execute('SELECT * FROM tasks ORDER BY id DESC LIMIT ?', (limit,)).fetchall()]

def get_task(task_id):
    with connect() as con:
        row = con.execute('SELECT * FROM tasks WHERE id=?', (task_id,)).fetchone()
        return dict(row) if row else None

def update_task(task_id, **fields):
    allowed = {'status','result_path','error'}
    pairs = [(k,v) for k,v in fields.items() if k in allowed]
    if not pairs: return
    pairs.append(('updated_at', now()))
    sql = ','.join(f'{k}=?' for k,_ in pairs)
    with connect() as con: con.execute(f'UPDATE tasks SET {sql} WHERE id=?', [v for _,v in pairs]+[task_id])

def event(task_id, agent, name, detail=''):
    with connect() as con:
        con.execute('INSERT INTO events(task_id,agent,event,detail,created_at) VALUES(?,?,?,?,?)', (task_id,agent,name,detail[:12000],now()))

def events(task_id, limit=100):
    with connect() as con:
        return [dict(r) for r in con.execute('SELECT * FROM events WHERE task_id=? ORDER BY id LIMIT ?', (task_id,limit)).fetchall()]

def save_lead(lead):
    with connect() as con:
        con.execute('INSERT OR IGNORE INTO leads(name,url,snippet,fit_score,rationale,outreach_draft,status,created_at) VALUES(?,?,?,?,?,?,?,?)', (lead.get('name','Unknown')[:300],lead['url'],lead.get('snippet','')[:3000],int(lead.get('fit_score',0)),lead.get('rationale','')[:3000],lead.get('outreach_draft','')[:6000],'draft_ready',now()))

def list_leads(limit=50):
    with connect() as con:
        return [dict(r) for r in con.execute('SELECT * FROM leads ORDER BY fit_score DESC,id DESC LIMIT ?', (limit,)).fetchall()]
