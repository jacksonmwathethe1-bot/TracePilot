import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
DEFAULT_DB = "tracepilot-history.sqlite3"
def connect(db_path=DEFAULT_DB):
    if str(db_path) != ":memory:":
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(str(db_path))
    db.row_factory = sqlite3.Row
    try:
        db.execute("""
            CREATE TABLE IF NOT EXISTS comparison_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                baseline TEXT NOT NULL,
                current TEXT NOT NULL,
                summary_json TEXT NOT NULL,
                result_json TEXT NOT NULL
            )
        """)
        db.commit()
    except Exception:
        db.close()
        raise
    return db
def save_run(result, db_path=DEFAULT_DB):
    db = connect(db_path)
    try:
        cursor = db.execute("""
            INSERT INTO comparison_runs
            (created_at, baseline, current, summary_json, result_json)
            VALUES (?, ?, ?, ?, ?)
        """, (
            datetime.now(timezone.utc).isoformat(timespec="seconds"),
            str(result.get("baseline", "")),
            str(result.get("current", "")),
            json.dumps(result.get("summary", {}), ensure_ascii=False),
            json.dumps(result, ensure_ascii=False),
        ))
        db.commit()
        return cursor.lastrowid
    finally:
        db.close()
def list_runs(db_path=DEFAULT_DB, limit=20):
    if limit < 1:
        raise ValueError("History limit must be at least 1.")
    db = connect(db_path)
    try:
        rows = db.execute("""
            SELECT id, created_at, baseline, current, summary_json
            FROM comparison_runs
            ORDER BY id DESC LIMIT ?
        """, (limit,)).fetchall()
    finally:
        db.close()
    result = []
    for row in rows:
        item = dict(row)
        item["summary"] = json.loads(item.pop("summary_json"))
        result.append(item)
    return result
def get_run(run_id, db_path=DEFAULT_DB):
    db = connect(db_path)
    try:
        row = db.execute(
            "SELECT result_json FROM comparison_runs WHERE id = ?",
            (run_id,)
        ).fetchone()
    finally:
        db.close()
    return json.loads(row["result_json"]) if row else None
