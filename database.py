"""SQLite data layer. All queries are parameterized; table/column names come from a whitelist.

Every row carries a user_id so the schema maps directly onto Supabase (Postgres) with
row-level security. SQLite itself does NOT isolate users: in this local build there is one
profile (user_id=1) and no login.
"""
from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent
STATUSES = ["Saved", "Preparing", "Applied", "Interview", "Offer", "Rejected"]
KINDS = ["Job", "Internship", "Government Exam", "GATE"]

COLUMNS = {
    "profile": ["name", "branch", "cgpa", "grad_year", "skills", "target_role", "daily_hours", "gate_year"],
    "opportunities": ["title", "org", "kind", "location", "deadline", "min_cgpa", "branches",
                      "required_skills", "url", "notes", "is_demo"],
    "resources": ["title", "provider", "url", "skill", "kind", "is_demo"],
    "study_tasks": ["title", "skill", "due_date", "minutes", "done", "completed_on", "opportunity_id", "is_demo"],
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS profile(user_id INTEGER PRIMARY KEY, name TEXT, branch TEXT, cgpa REAL,
  grad_year INTEGER, skills TEXT, target_role TEXT, daily_hours REAL DEFAULT 2, gate_year INTEGER);
CREATE TABLE IF NOT EXISTS opportunities(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
  title TEXT NOT NULL, org TEXT, kind TEXT NOT NULL, location TEXT, deadline TEXT, min_cgpa REAL,
  branches TEXT, required_skills TEXT, url TEXT, notes TEXT, is_demo INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS applications(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
  opportunity_id INTEGER NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
  status TEXT NOT NULL DEFAULT 'Saved', applied_on TEXT, UNIQUE(user_id, opportunity_id));
CREATE TABLE IF NOT EXISTS resources(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL DEFAULT 0,
  title TEXT NOT NULL, provider TEXT, url TEXT NOT NULL, skill TEXT NOT NULL, kind TEXT, is_demo INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS study_tasks(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
  title TEXT NOT NULL, skill TEXT, due_date TEXT, minutes INTEGER NOT NULL DEFAULT 30, done INTEGER DEFAULT 0,
  completed_on TEXT, opportunity_id INTEGER, is_demo INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS gate_progress(user_id INTEGER NOT NULL, subject TEXT NOT NULL, pct INTEGER DEFAULT 0,
  PRIMARY KEY(user_id, subject));
CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT);
CREATE INDEX IF NOT EXISTS idx_opp_user ON opportunities(user_id);
CREATE INDEX IF NOT EXISTS idx_task_user ON study_tasks(user_id, due_date);
"""

PROFILE_DEFAULTS = {"name": "Student", "branch": "cse", "cgpa": 7.5, "grad_year": 2027,
                    "skills": "python, git", "target_role": "Software Engineer",
                    "daily_hours": 2.0, "gate_year": None}


def db_path() -> str:
    return os.environ.get("CAREEROS_DB", str(ROOT / "data" / "careeros.db"))


@contextmanager
def connect(path: str | None = None):
    p = path or db_path()
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(p)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(path: str | None = None) -> None:
    with connect(path) as c:
        c.executescript(SCHEMA)


def query(sql: str, params: tuple = (), path: str | None = None) -> pd.DataFrame:
    with connect(path) as c:
        return pd.read_sql_query(sql, c, params=params)


def _check(table: str) -> list[str]:
    if table not in COLUMNS:
        raise ValueError(f"Unknown table: {table}")
    return COLUMNS[table]


def insert(table: str, user_id: int, data: dict, path: str | None = None) -> int:
    cols = [c for c in data if c in _check(table)]
    sql = f"INSERT INTO {table}(user_id,{','.join(cols)}) VALUES (?,{','.join('?' * len(cols))})"
    with connect(path) as c:
        return c.execute(sql, (user_id, *[data[k] for k in cols])).lastrowid


def update(table: str, user_id: int, row_id: int, data: dict, path: str | None = None) -> None:
    cols = [c for c in data if c in _check(table)]
    if not cols:
        return
    sql = f"UPDATE {table} SET {','.join(f'{k}=?' for k in cols)} WHERE id=? AND user_id=?"
    with connect(path) as c:
        c.execute(sql, (*[data[k] for k in cols], row_id, user_id))


def delete(table: str, user_id: int, row_id: int, path: str | None = None) -> None:
    _check(table)
    with connect(path) as c:
        c.execute(f"DELETE FROM {table} WHERE id=? AND user_id=?", (row_id, user_id))


# ---- profile -------------------------------------------------------------
def get_profile(user_id: int, path: str | None = None) -> dict:
    with connect(path) as c:
        row = c.execute("SELECT * FROM profile WHERE user_id=?", (user_id,)).fetchone()
    prof = dict(PROFILE_DEFAULTS)
    if row:
        prof.update({k: row[k] for k in COLUMNS["profile"] if row[k] is not None})
    return prof


def save_profile(user_id: int, data: dict, path: str | None = None) -> None:
    merged = {**get_profile(user_id, path), **{k: v for k, v in data.items() if k in COLUMNS["profile"]}}
    cols = COLUMNS["profile"]
    sql = (f"INSERT INTO profile(user_id,{','.join(cols)}) VALUES (?,{','.join('?' * len(cols))}) "
           f"ON CONFLICT(user_id) DO UPDATE SET {','.join(f'{k}=excluded.{k}' for k in cols)}")
    with connect(path) as c:
        c.execute(sql, (user_id, *[merged[k] for k in cols]))


# ---- opportunities & applications ----------------------------------------
def list_opportunities(user_id: int, path: str | None = None) -> pd.DataFrame:
    return query(
        "SELECT o.*, COALESCE(a.status,'Saved') AS status, a.applied_on FROM opportunities o "
        "LEFT JOIN applications a ON a.opportunity_id=o.id AND a.user_id=o.user_id "
        "WHERE o.user_id=? ORDER BY (o.deadline IS NULL), o.deadline", (user_id,), path)


def set_status(user_id: int, opp_id: int, status: str, applied_on: str | None = None,
               path: str | None = None) -> None:
    if status not in STATUSES:
        raise ValueError(f"Invalid status: {status}")
    with connect(path) as c:
        owned = c.execute("SELECT 1 FROM opportunities WHERE id=? AND user_id=?", (opp_id, user_id)).fetchone()
        if not owned:
            raise ValueError("Opportunity not found")
        c.execute("INSERT INTO applications(user_id,opportunity_id,status,applied_on) VALUES (?,?,?,?) "
                  "ON CONFLICT(user_id,opportunity_id) DO UPDATE SET status=excluded.status, "
                  "applied_on=COALESCE(excluded.applied_on, applications.applied_on)",
                  (user_id, opp_id, status, applied_on))


# ---- tasks ---------------------------------------------------------------
def list_tasks(user_id: int, path: str | None = None) -> pd.DataFrame:
    return query("SELECT * FROM study_tasks WHERE user_id=? ORDER BY done, (due_date IS NULL), due_date, id",
                 (user_id,), path)


def set_task_done(user_id: int, task_id: int, done: bool, on: str | None, path: str | None = None) -> None:
    update("study_tasks", user_id, task_id,
           {"done": int(done), "completed_on": on if done else None}, path)


# ---- resources -----------------------------------------------------------
def list_resources(user_id: int, path: str | None = None) -> pd.DataFrame:
    return query("SELECT * FROM resources WHERE user_id IN (0, ?) ORDER BY skill, title", (user_id,), path)


# ---- GATE progress -------------------------------------------------------
def get_gate_progress(user_id: int, path: str | None = None) -> dict:
    df = query("SELECT subject, pct FROM gate_progress WHERE user_id=?", (user_id,), path)
    return dict(zip(df["subject"], df["pct"]))


def set_gate_progress(user_id: int, subject: str, pct: int, path: str | None = None) -> None:
    pct = max(0, min(100, int(pct)))
    with connect(path) as c:
        c.execute("INSERT INTO gate_progress(user_id,subject,pct) VALUES (?,?,?) "
                  "ON CONFLICT(user_id,subject) DO UPDATE SET pct=excluded.pct", (user_id, subject, pct))


# ---- meta / demo data ----------------------------------------------------
def get_meta(key: str, path: str | None = None) -> str | None:
    with connect(path) as c:
        row = c.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
    return row["value"] if row else None


def set_meta(key: str, value: str, path: str | None = None) -> None:
    with connect(path) as c:
        c.execute("INSERT INTO meta(key,value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                  (key, value))


def clear_demo(user_id: int, path: str | None = None) -> None:
    with connect(path) as c:
        c.execute("DELETE FROM opportunities WHERE user_id=? AND is_demo=1", (user_id,))
        c.execute("DELETE FROM study_tasks WHERE user_id=? AND is_demo=1", (user_id,))
