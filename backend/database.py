import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

DB_PATH = Path(__file__).resolve().parent / "data" / "app.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    schema = """
    CREATE TABLE IF NOT EXISTS conversation_session (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_uuid TEXT NOT NULL UNIQUE,
        started_at DATETIME NOT NULL,
        ended_at DATETIME,
        debug_mode INTEGER NOT NULL DEFAULT 0,
        status TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS complaint (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_uuid TEXT NOT NULL,
        raw_text TEXT NOT NULL,
        summary_text TEXT NOT NULL,
        category TEXT NOT NULL,
        severity TEXT NOT NULL,
        handling_type TEXT NOT NULL,
        handling_desc TEXT,
        is_confirmed INTEGER NOT NULL,
        created_at DATETIME NOT NULL,
        FOREIGN KEY (session_uuid) REFERENCES conversation_session(session_uuid)
    );

    CREATE TABLE IF NOT EXISTS complaint_handling (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        complaint_id INTEGER NOT NULL,
        handler_name TEXT,
        handler_dept TEXT,
        status TEXT NOT NULL,
        note TEXT,
        updated_at DATETIME NOT NULL,
        FOREIGN KEY (complaint_id) REFERENCES complaint(id)
    );

    CREATE TABLE IF NOT EXISTS log_entry (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_uuid TEXT NOT NULL,
        step TEXT NOT NULL,
        level TEXT NOT NULL,
        message TEXT NOT NULL,
        payload TEXT,
        created_at DATETIME NOT NULL,
        FOREIGN KEY (session_uuid) REFERENCES conversation_session(session_uuid)
    );
    """

    with get_connection() as conn:
        conn.executescript(schema)


def create_session(session_uuid: str, debug_mode: bool) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO conversation_session (session_uuid, started_at, debug_mode, status)
            VALUES (?, ?, ?, ?)
            """,
            (session_uuid, datetime.utcnow().isoformat(), int(debug_mode), "IN_PROGRESS"),
        )


def update_session_status(session_uuid: str, status: str) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE conversation_session
            SET status = ?, ended_at = ?
            WHERE session_uuid = ?
            """,
            (status, datetime.utcnow().isoformat(), session_uuid),
        )


def insert_complaint(data: Dict[str, Any]) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO complaint (
                session_uuid, raw_text, summary_text, category, severity,
                handling_type, handling_desc, is_confirmed, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["session_uuid"],
                data["raw_text"],
                data["summary_text"],
                data["category"],
                data["severity"],
                data["handling_type"],
                data.get("handling_desc"),
                int(data.get("is_confirmed", False)),
                datetime.utcnow().isoformat(),
            ),
        )
        complaint_id = cur.lastrowid
    return int(complaint_id)


def insert_log(session_uuid: str, step: str, level: str, message: str, payload: Optional[Dict[str, Any]] = None) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO log_entry (session_uuid, step, level, message, payload, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                session_uuid,
                step,
                level,
                message,
                json.dumps(payload, ensure_ascii=False) if payload is not None else None,
                datetime.utcnow().isoformat(),
            ),
        )


def fetch_logs(session_uuid: Optional[str] = None) -> List[Dict[str, Any]]:
    query = "SELECT step, level, message, payload, created_at FROM log_entry"
    params: Iterable[Any] = []
    if session_uuid:
        query += " WHERE session_uuid = ?"
        params = [session_uuid]
    query += " ORDER BY created_at ASC"

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]
