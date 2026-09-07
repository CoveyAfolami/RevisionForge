"""Repository for the resources table — textbook PDFs and other inputs."""

import hashlib
import sqlite3
from pathlib import Path

from ..connection import utc_now_iso


class ResourceRepository:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    @staticmethod
    def hash_file(path: str | Path) -> str:
        """SHA-256 of a file's bytes — answers 'is this the same file?' exactly."""
        digest = hashlib.sha256()
        with open(path, "rb") as file:
            for block in iter(lambda: file.read(8192), b""):
                digest.update(block)
        return digest.hexdigest()

    def create(self, path: str, filename: str, file_hash: str, subject: str | None = None,
               resource_type: str = "pdf") -> int:
        with self.connection:
            cursor = self.connection.execute(
                "INSERT INTO resources (path, filename, file_hash, resource_type, subject, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (path, filename, file_hash, resource_type, subject, utc_now_iso()),
            )
        return cursor.lastrowid

    def find_by_hash(self, file_hash: str) -> dict | None:
        """Exact-duplicate detection for whole files (repeat prevention)."""
        row = self.connection.execute(
            "SELECT * FROM resources WHERE file_hash = ?", (file_hash,)
        ).fetchone()
        return dict(row) if row else None

    def get(self, resource_id: int) -> dict | None:
        row = self.connection.execute(
            "SELECT * FROM resources WHERE id = ?", (resource_id,)
        ).fetchone()
        return dict(row) if row else None

    def mark_processed(self, resource_id: int) -> None:
        with self.connection:
            self.connection.execute(
                "UPDATE resources SET status = 'processed', processed_at = ? WHERE id = ?",
                (utc_now_iso(), resource_id),
            )

    def list_all(self) -> list[dict]:
        rows = self.connection.execute("SELECT * FROM resources ORDER BY id DESC").fetchall()
        return [dict(row) for row in rows]
