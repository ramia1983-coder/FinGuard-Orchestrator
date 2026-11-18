"""SQLite repository for demo cases. Not production multi-user storage."""
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

def connect(path='finguard.db'):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    con=sqlite3.connect(path)
    con.row_factory=sqlite3.Row
    con.execute('PRAGMA foreign_keys=ON')
    con.executescript('''CREATE TABLE IF NOT EXISTS batches(batch_id TEXT PRIMARY KEY, created_at TEXT, transaction_count INTEGER, error_count INTEGER);
    CREATE TABLE IF NOT EXISTS transactions(batch_id TEXT, transaction_id TEXT, payload TEXT NOT NULL, PRIMARY KEY(batch_id,transaction_id), FOREIGN KEY(batch_id) REFERENCES batches(batch_id));
    CREATE TABLE IF NOT EXISTS cases(case_id TEXT PRIMARY KEY,batch_id TEXT NOT NULL,typology TEXT,status TEXT, payload TEXT, assessment TEXT, created_at TEXT, FOREIGN KEY(batch_id) REFERENCES batches(batch_id));
    CREATE TABLE IF NOT EXISTS reviews(id INTEGER PRIMARY KEY AUTOINCREMENT,case_id TEXT,decision TEXT,reviewer TEXT,notes TEXT,created_at TEXT,FOREIGN KEY(case_id) REFERENCES cases(case_id));''')
    return con

def save_batch(con,batch_id,transactions,cases,errors):
    now=datetime.now(timezone.utc).isoformat()
    with con:
        con.execute('INSERT INTO batches VALUES(?,?,?,?)',(batch_id,now,len(transactions),len(errors)))
        con.executemany('INSERT INTO transactions VALUES(?,?,?)',[(batch_id,t['transaction_id'],json.dumps(t)) for t in transactions])
        con.executemany('INSERT INTO cases VALUES(?,?,?,?,?,?,?)',[(c['case_id'],batch_id,c['typology'],'pending_review',json.dumps(c),None,now) for c in cases])

def list_cases(con,batch_id=None):
    sql='SELECT case_id,batch_id,typology,status,payload,assessment FROM cases'
    rows=con.execute(sql+' WHERE batch_id=? ORDER BY created_at DESC' if batch_id else sql+' ORDER BY created_at DESC',(batch_id,) if batch_id else ()).fetchall()
    return [{**dict(r),'payload':json.loads(r['payload']),'assessment':json.loads(r['assessment']) if r['assessment'] else None} for r in rows]

def get_case(con,case_id):
    row=con.execute('SELECT * FROM cases WHERE case_id=?',(case_id,)).fetchone()
    return dict(row) if row else None

def get_case_transactions(con,case_id):
    row=get_case(con,case_id)
    if not row:return []
    ids=json.loads(row['payload'])['transaction_ids']
    return [json.loads(r['payload']) for r in con.execute('SELECT payload FROM transactions WHERE batch_id=?',(row['batch_id'],)) if json.loads(r['payload'])['transaction_id'] in set(ids)]

def save_assessment(con,case_id,assessment):
    with con:con.execute('UPDATE cases SET assessment=? WHERE case_id=?',(json.dumps(assessment),case_id))

def review_case(con,case_id,decision,reviewer,notes=''):
    if decision not in {'approved','rejected','needs_revision'}:raise ValueError('Invalid decision')
    if not reviewer.strip():raise ValueError('Reviewer required')
    if not get_case(con,case_id):raise ValueError('Unknown case')
    with con:
        con.execute('INSERT INTO reviews(case_id,decision,reviewer,notes,created_at) VALUES(?,?,?,?,?)',(case_id,decision,reviewer.strip(),notes,datetime.now(timezone.utc).isoformat()))
        con.execute('UPDATE cases SET status=? WHERE case_id=?',(decision,case_id))
