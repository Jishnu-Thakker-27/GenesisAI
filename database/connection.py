import sqlite3
from contextlib import contextmanager
from typing import Generator
from config import DB_PATH
from database.tables import initialize_database

def init_db():
    """Initializes the database schema and seeds metadata."""
    initialize_database(DB_PATH)

@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    """Provides a transactional SQLite connection with Row factory configured."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # Enforce foreign key constraints
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
