import sqlite3
from datetime import datetime, timezone
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
        con.executescript("""
        CREATE TABLE IF NOT EXISTS tasks(id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, description TEXT NOT NULL DEFAULT '', status TEXT NOT NULL DEFAULT 'queued', result_path TEXT, error TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY AUTOINCREMENT, task_id INTEGER, agent TEXT NOT NULL, event TEXT NOT NULL, detail TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS leads(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, url TEXT NOT NULL UNIQUE, snippet TEXT NOT NULL DEFAULT '', fit_score INTEGER NOT NULL DEFAULT 0, rationale TEXT NOT NULL DEFAULT '', outreach_draft TEXT NOT NULL DEFAULT '', status TEXT NOT NULL DEFAULT 'discovered', created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS projects(id INTEGER PRIMARY KEY AUTOINCREMENT, lead_id INTEGER, name TEXT NOT NULL, scope TEXT NOT NULL DEFAULT '', status TEXT NOT NULL DEFAULT 'proposed', budget_paise INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL, updated_at TEXT NOT NULL, FOREIGN KEY(lead_id) REFERENCES leads(id));
        CREATE TABLE IF NOT EXISTS invoices(id INTEGER PRIMARY KEY AUTOINCREMENT, project_id INTEGER NOT NULL, description TEXT NOT NULL, amount_paise INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'draft', due_date TEXT, created_at TEXT NOT NULL, FOREIGN KEY(project_id) REFERENCES projects(id));
        CREATE TABLE IF NOT EXISTS lead_notes(id INTEGER PRIMARY KEY AUTOINCREMENT, lead_id INTEGER NOT NULL, note TEXT NOT NULL, created_at TEXT NOT NULL, FOREIGN KEY(lead_id) REFERENCES leads(id));
        """)

def add_task(title, description=''):
    stamp = now()
    with connect() as con:
        cur = con.execute("INSERT INTO tasks(title,description,status,created_at,updated_at) VALUES(?,?,'queued',?,?)", (title, description, stamp, stamp))
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
    with connect() as con:
        con.execute(f'UPDATE tasks SET {sql} WHERE id=?', [v for _,v in pairs]+[task_id])

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

def update_lead_status(lead_id, status, note=''):
    allowed={'discovered','draft_ready','approved_for_contact','contacted','replied','qualified','converted','rejected'}
    if status not in allowed:
        raise ValueError('Invalid lead status')
    with connect() as con:
        cur=con.execute('UPDATE leads SET status=? WHERE id=?',(status,lead_id))
        if cur.rowcount == 0: return False
        if note.strip():
            con.execute('INSERT INTO lead_notes(lead_id,note,created_at) VALUES(?,?,?)',(lead_id,note.strip()[:4000],now()))
        return True

def create_project(name, scope='', lead_id=None, budget_paise=0):
    stamp=now()
    with connect() as con:
        cur=con.execute("INSERT INTO projects(lead_id,name,scope,status,budget_paise,created_at,updated_at) VALUES(?,?,?,'proposed',?,?,?)",(lead_id,name[:300],scope[:12000],max(0,int(budget_paise)),stamp,stamp))
        return cur.lastrowid

def list_projects(limit=100):
    with connect() as con:
        return [dict(r) for r in con.execute('SELECT * FROM projects ORDER BY id DESC LIMIT ?', (limit,)).fetchall()]

def update_project_status(project_id, status):
    allowed={'proposed','awaiting_approval','active','blocked','delivered','cancelled'}
    if status not in allowed: raise ValueError('Invalid project status')
    with connect() as con:
        cur=con.execute('UPDATE projects SET status=?,updated_at=? WHERE id=?',(status,now(),project_id))
        return cur.rowcount > 0

def create_invoice(project_id, description, amount_paise, due_date=None):
    if int(amount_paise) < 0: raise ValueError('Invoice amount cannot be negative')
    with connect() as con:
        if not con.execute('SELECT id FROM projects WHERE id=?',(project_id,)).fetchone(): return None
        cur=con.execute("INSERT INTO invoices(project_id,description,amount_paise,status,due_date,created_at) VALUES(?,?,?,'draft',?,?)",(project_id,description[:1000],int(amount_paise),due_date,now()))
        return cur.lastrowid

def list_invoices(limit=100):
    with connect() as con:
        return [dict(r) for r in con.execute('SELECT * FROM invoices ORDER BY id DESC LIMIT ?', (limit,)).fetchall()]
