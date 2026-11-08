
import sqlite3
from contextlib import closing
from datetime import datetime, timezone

from pathlib import Path

DB_PATH = str(Path(__file__).resolve().parent / "school.db")


def database_path():
    from flask import current_app, has_app_context
    return current_app.config.get('DATABASE', DB_PATH) if has_app_context() else DB_PATH


def init_audit_table():
    """Create the audit log table if it does not exist."""
    with closing(sqlite3.connect(database_path())) as conn, conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user_id TEXT,
                action TEXT NOT NULL,
                success INTEGER NOT NULL,
                details TEXT
            )
        """)


def log_event(user_id, action, success, details=""):
    """Record a security-related event."""
    init_audit_table()

    timestamp = datetime.now(timezone.utc).isoformat()

    with closing(sqlite3.connect(database_path())) as conn, conn:
        conn.execute("""
            INSERT INTO audit_logs
            (timestamp, user_id, action, success, details)
            VALUES (?, ?, ?, ?, ?)
        """, (
            timestamp,
            str(user_id) if user_id is not None else None,
            action,
            int(success),
            details
        ))

