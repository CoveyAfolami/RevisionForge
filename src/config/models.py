"""Dataclasses representing the application configuration.

Defined top-down in dependency order: simple types first, then the
composite AppConfig. Python reads modules top-to-bottom, so referenced
classes must exist before they are used.
"""

from dataclasses import dataclass


@dataclass
class Settings:
    application_name: str
    database_path: str = "data/revision_forge.db"
    log_level: str = "INFO"
    log_file: str = "logs/revision_forge.log"


@dataclass
class SubjectConfig:
    name: str
    exam_board: str
    qualification: str
    anki_deck: str
    syllabus_code: str | None = None


@dataclass
class NoteTypeRule:
    """How and when a particular Anki note type should be used."""
    note_type: str
    use_for: list[str]
    delimiter: str | None = None
    required_tag: str | None = None
    deck_suffix: str | None = None
    applies_to_subjects: list[str] | None = None
    basic_qa_format: str | None = None


@dataclass
class FlashcardPreferences:
    one_idea_per_card: bool
    exam_focused: bool
    use_mark_scheme_terminology: bool
    concise: bool
    default_note_type: str
    note_type_rules: dict[str, NoteTypeRule]


@dataclass
class ApprovalConfig:
    required_for_anki_writes: bool
    allow_bulk_approve: bool


@dataclass
class AppConfig:
    """Everything the application needs to run, loaded from config/."""
    settings: Settings
    subjects: list[SubjectConfig]
    flashcard_preferences: FlashcardPreferences
    approval: ApprovalConfig
