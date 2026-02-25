import os
import sqlite3

def get_connection():
    """
    Creates and returns a DB connection.
    """
    output_dir = os.path.join(os.path.dirname(__file__), "outputs")
    os.makedirs(output_dir, exist_ok=True)

    db_path = os.path.join(output_dir, "summaries.db")
    return sqlite3.connect(db_path)

def init_db():
    """
    Initializes database and creates table if not exists.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                model TEXT,
                original_length INTEGER,
                summary_length INTEGER,
                original_text TEXT,
                summary TEXT
            )
        """)
        conn.commit()

