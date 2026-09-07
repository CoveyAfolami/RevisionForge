"""SQLite schema definitions.

The schema version is stored in PRAGMA user_version so future migrations
can upgrade old databases in place.
"""

SCHEMA_VERSION = 1

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS resources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT NOT NULL,
    filename TEXT NOT NULL,
    file_hash TEXT NOT NULL UNIQUE,
    resource_type TEXT NOT NULL DEFAULT 'pdf',
    subject TEXT,
    created_at TEXT NOT NULL,
    processed_at TEXT,
    status TEXT NOT NULL DEFAULT 'new',
    metadata_json TEXT
);

CREATE TABLE IF NOT EXISTS processing_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    status TEXT NOT NULL DEFAULT 'running',
    user_request TEXT,
    subject TEXT,
    resource_id INTEGER REFERENCES resources(id),
    cards_generated INTEGER NOT NULL DEFAULT 0,
    cards_approved INTEGER NOT NULL DEFAULT 0,
    cards_added INTEGER NOT NULL DEFAULT 0,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    processing_run_id INTEGER NOT NULL REFERENCES processing_runs(id),
    subject TEXT NOT NULL,
    topic TEXT,
    front TEXT NOT NULL,
    back TEXT NOT NULL,
    extra TEXT,
    note_type TEXT NOT NULL,
    tags_json TEXT NOT NULL DEFAULT '[]',
    status TEXT NOT NULL DEFAULT 'generated',
    content_hash TEXT NOT NULL,
    anki_note_id INTEGER,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_cards_content_hash ON cards(content_hash);
CREATE INDEX IF NOT EXISTS idx_cards_status ON cards(status);
CREATE INDEX IF NOT EXISTS idx_processing_runs_subject ON processing_runs(subject);
"""
