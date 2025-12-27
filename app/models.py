import sqlite3
from datetime import datetime
from app.config import DATABASE_URL

def get_db():
    """
    Returns a SQLite connection.
    """
    if not DATABASE_URL.startswith("sqlite:///"):
        raise RuntimeError("Only sqlite DATABASE_URL is supported")

    db_path = DATABASE_URL.replace("sqlite:///", "")
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    Create tables if they do not exist.
    """
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        message_id TEXT PRIMARY KEY,
        from_msisdn TEXT NOT NULL,
        to_msisdn TEXT NOT NULL,
        ts TEXT NOT NULL,
        text TEXT,
        created_at TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()
