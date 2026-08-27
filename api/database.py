import sqlite3
from datetime import datetime

DB_PATH = "tickets.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT,
            subject TEXT,
            body TEXT,
            category TEXT,
            summary TEXT,
            draft_reply TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_ticket(sender, subject, body, category=None, summary=None, draft_reply=None):
    conn = get_connection()
    cursor = conn.execute(
        """
        INSERT INTO tickets (sender, subject, body, category, summary, draft_reply, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (sender, subject, body, category, summary, draft_reply, datetime.utcnow().isoformat())
    )
    conn.commit()
    ticket_id = cursor.lastrowid
    conn.close()
    return ticket_id


def get_all_tickets():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM tickets ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(row) for row in rows]