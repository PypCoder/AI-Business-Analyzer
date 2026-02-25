from datetime import datetime
from .init_db import get_connection, init_db

def write_summary(original_text: str, summary: str, model_name: str):
    """
    Writes a summary entry to the database.
    """
    init_db()

    timestamp = datetime.utcnow().isoformat()

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO summaries (
                timestamp,
                model,
                original_length,
                summary_length,
                original_text,
                summary
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            timestamp,
            model_name,
            len(original_text),
            len(summary),
            original_text,
            summary
        ))
        conn.commit()