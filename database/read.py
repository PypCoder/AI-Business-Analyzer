# database/read.py

from .init_db import get_connection, init_db


def search_related_summaries(goal: str, limit: int = 3):
    """
    Search previous summaries related to current goal.
    Basic LIKE search (can upgrade to embeddings later).
    """
    init_db()

    keyword = f"%{goal}%"

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT summary, original_text, timestamp
            FROM summaries
            WHERE original_text LIKE ?
            ORDER BY id DESC
            LIMIT ?
        """, (keyword, limit))

        results = cursor.fetchall()

    return [r[0] for r in results]