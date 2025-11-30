import sqlite3
from typing import List, Tuple, Optional

DB_PATH = "documents.db"


def get_connection() -> sqlite3.Connection:
    """Create a new SQLite connection."""
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    """Create the documents table if it does not exist."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_type TEXT,
                path_or_url TEXT,
                raw_text TEXT,
                summary TEXT
            )
            """
        )
        conn.commit()


def add_document(
    source_type: str,
    path_or_url: str,
    raw_text: str,
    summary: Optional[str] = None
) -> int:
    """Insert a new document and return its ID."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO documents (source_type, path_or_url, raw_text, summary) "
            "VALUES (?, ?, ?, ?)",
            (source_type, path_or_url, raw_text, summary),
        )
        conn.commit()
        return cur.lastrowid


def get_all_documents() -> List[Tuple[int, str, str, str, Optional[str]]]:
    """Fetch all documents as (id, source_type, path_or_url, raw_text, summary)."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, source_type, path_or_url, raw_text, summary FROM documents"
        )
        rows = cur.fetchall()
    return rows


def update_summary(doc_id: int, summary: str) -> None:
    """Update the summary field for a document."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE documents SET summary = ? WHERE id = ?",
                    (summary, doc_id))
        conn.commit()


def delete_document(doc_id: int) -> None:
    """Delete a single document by ID."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        conn.commit()


def clear_all_documents() -> None:
    """Delete all documents from the table (used for 'New Session')."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM documents")
        conn.commit()
