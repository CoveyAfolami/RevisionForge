"""Repository for the processing_runs table — one row per execution."""

import sqlite3

from ..connection import utc_now_iso


class ProcessingRunRepository:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def create(self, user_request: str | None = None, subject: str | None = None,
               resource_id: int | None = None) -> int:
        """Record that a run has started, and return its id."""
        with self.connection:
            cursor = self.connection.execute(
                "INSERT INTO processing_runs (started_at, user_request, subject, resource_id) "
                "VALUES (?, ?, ?, ?)",
                (utc_now_iso(), user_request, subject, resource_id),
            )
        return cursor.lastrowid

    def get(self, run_id: int) -> dict | None:
        row = self.connection.execute(
            "SELECT * FROM processing_runs WHERE id = ?", (run_id,)
        ).fetchone()
        return dict(row) if row else None

    def complete(self, run_id: int, cards_generated: int = 0, cards_approved: int = 0,
                 cards_added: int = 0) -> None:
        with self.connection:
            self.connection.execute(
                "UPDATE processing_runs SET completed_at = ?, status = 'completed', "
                "cards_generated = ?, cards_approved = ?, cards_added = ? WHERE id = ?",
                (utc_now_iso(), cards_generated, cards_approved, cards_added, run_id),
            )

    def fail(self, run_id: int, error_message: str) -> None:
        with self.connection:
            self.connection.execute(
                "UPDATE processing_runs SET completed_at = ?, status = 'failed', "
                "error_message = ? WHERE id = ?",
                (utc_now_iso(), error_message, run_id),
            )

    def list_recent(self, limit: int = 20) -> list[dict]:
        rows = self.connection.execute(
            "SELECT * FROM processing_runs ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(row) for row in rows]
