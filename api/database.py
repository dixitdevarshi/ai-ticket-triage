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
            urgency TEXT,
            summary TEXT,
            draft_reply TEXT,
            confidence TEXT,
            needs_review INTEGER DEFAULT 0,
            review_reason TEXT,
            corrected_category TEXT,
            corrected_urgency TEXT,
            reviewed INTEGER DEFAULT 0,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_ticket(sender, subject, body, category=None, urgency=None, summary=None, draft_reply=None,
                 confidence=None, needs_review=0, review_reason=None):
    conn = get_connection()
    cursor = conn.execute(
        """
        INSERT INTO tickets (sender, subject, body, category, urgency, summary, draft_reply,
                              confidence, needs_review, review_reason, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (sender, subject, body, category, urgency, summary, draft_reply,
         confidence, needs_review, review_reason, datetime.utcnow().isoformat())
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


def get_tickets_needing_review():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM tickets WHERE needs_review = 1 AND reviewed = 0 ORDER BY id DESC"
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def submit_correction(ticket_id, corrected_category=None, corrected_urgency=None):
    conn = get_connection()
    conn.execute(
        "UPDATE tickets SET corrected_category = ?, corrected_urgency = ?, reviewed = 1 WHERE id = ?",
        (corrected_category, corrected_urgency, ticket_id)
    )
    conn.commit()
    conn.close()


def get_past_corrections(limit=3):
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT subject, body, corrected_category, corrected_urgency
        FROM tickets
        WHERE reviewed = 1 AND (corrected_category IS NOT NULL OR corrected_urgency IS NOT NULL)
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]
