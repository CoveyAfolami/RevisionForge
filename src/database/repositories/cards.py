"""Repository for the cards table — every generated flashcard's lifecycle."""

import json
import sqlite3

from ...cards.hashing import hash_card
from ..connection import utc_now_iso


class CardRepository:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def create(self, processing_run_id: int, subject: str, front: str, back: str,
               note_type: str, topic: str | None = None, extra: str | None = None,
               tags: list[str] | None = None, status: str = "generated") -> int:
        """Store a card. The content hash is computed, never trusted from outside."""
        now = utc_now_iso()
        with self.connection:
            cursor = self.connection.execute(
                "INSERT INTO cards (processing_run_id, subject, topic, front, back, extra, "
                "note_type, tags_json, status, content_hash, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    processing_run_id, subject, topic, front, back, extra, note_type,
                    json.dumps(tags or []), status, hash_card(front, back), now, now,
                ),
            )
        return cursor.lastrowid

    def get(self, card_id: int) -> dict | None:
        row = self.connection.execute("SELECT * FROM cards WHERE id = ?", (card_id,)).fetchone()
        return dict(row) if row else None

    def find_by_content_hash(self, content_hash: str) -> dict | None:
        """Exact-duplicate detection for cards (front + back, normalised)."""
        row = self.connection.execute(
            "SELECT * FROM cards WHERE content_hash = ?", (content_hash,)
        ).fetchone()
        return dict(row) if row else None

    def update_status(self, card_id: int, status: str, anki_note_id: int | None = None) -> None:
        with self.connection:
            self.connection.execute(
                "UPDATE cards SET status = ?, anki_note_id = ?, updated_at = ? WHERE id = ?",
                (status, anki_note_id, utc_now_iso(), card_id),
            )

    def list_by_run(self, run_id: int) -> list[dict]:
        rows = self.connection.execute(
            "SELECT * FROM cards WHERE processing_run_id = ? ORDER BY id", (run_id,)
        ).fetchall()
        return [dict(row) for row in rows]

    def list_by_status(self, status: str) -> list[dict]:
        rows = self.connection.execute(
            "SELECT * FROM cards WHERE status = ? ORDER BY id", (status,)
        ).fetchall()
        return [dict(row) for row in rows]

    def count_by_hash(self, content_hash: str) -> int:
        """How many stored cards share this hash — for intra-batch duplicate checks."""
        return self.connection.execute(
            "SELECT COUNT(*) FROM cards WHERE content_hash = ?", (content_hash,)
        ).fetchone()[0]
