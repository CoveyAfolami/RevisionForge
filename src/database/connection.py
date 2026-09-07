"""Database connection management."""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from ..observability.errors import DatabaseError
from .schema import SCHEMA_SQL, SCHEMA_VERSION


def utc_now_iso() -> str:
    """Current UTC time as an ISO-8601 string, used for all timestamps."""
    return datetime.now(timezone.utc).isoformat()


def connect(db_path: str = "data/revision_forge.db") -> sqlite3.Connection:
    """Open the database, creating/migrating the schema if needed."""
    try:
        path = Path(db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        _apply_schema(connection)
        return connection
    except sqlite3.Error as error:
        raise DatabaseError(f"Could not open database at {db_path}: {error}") from error


def _apply_schema(connection: sqlite3.Connection) -> None:
    """Create the schema if the database is older than SCHEMA_VERSION."""
    current_version = connection.execute("PRAGMA user_version").fetchone()[0]
    if current_version >= SCHEMA_VERSION:
        return
    try:
        connection.executescript(SCHEMA_SQL)
        connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
    except sqlite3.Error as error:
        raise DatabaseError(f"Could not apply database schema: {error}") from error
