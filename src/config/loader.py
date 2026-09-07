"""Load configuration from config/settings.json and config/subjects.json.

Never hard-code user-specific values — this module is the single place
where raw JSON becomes typed, validated configuration objects.
"""

import json
from pathlib import Path

from ..observability.errors import ConfigurationError
from .models import (
    AppConfig,
    ApprovalConfig,
    FlashcardPreferences,
    NoteTypeRule,
    Settings,
    SubjectConfig,
)

SETTINGS_PATH = Path("config/settings.json")
SUBJECTS_PATH = Path("config/subjects.json")


def _read_json(path: Path) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError as error:
        raise ConfigurationError(f"Configuration file not found: {path}") from error
    except json.JSONDecodeError as error:
        raise ConfigurationError(f"Invalid JSON in {path}: {error}") from error


def load_config() -> AppConfig:
    """Load the complete application configuration."""
    return AppConfig(
        settings=load_settings(),
        subjects=load_subjects(),
        flashcard_preferences=load_flashcard_preferences(),
        approval=load_approval(),
    )


def load_settings() -> Settings:
    data = _read_json(SETTINGS_PATH)
    try:
        return Settings(
            application_name=data["application_name"],
            database_path=data.get("database", {}).get("path", Settings.database_path),
            log_level=data.get("logging", {}).get("level", Settings.log_level),
            log_file=data.get("logging", {}).get("file", Settings.log_file),
        )
    except KeyError as error:
        raise ConfigurationError(f"Missing required setting: {error}") from error


def load_subject(subject_data: dict, subject_name: str) -> SubjectConfig:
    try:
        return SubjectConfig(
            name=subject_name,
            exam_board=subject_data["exam_board"],
            qualification=subject_data["qualification"],
            anki_deck=subject_data["anki_deck"],
            syllabus_code=subject_data.get("syllabus_code"),
        )
    except KeyError as error:
        raise ConfigurationError(
            f"Subject '{subject_name}' is missing required field: {error}"
        ) from error


def load_subjects() -> list[SubjectConfig]:
    data = _read_json(SUBJECTS_PATH)
    subjects = data.get("subjects", {})
    if not subjects:
        raise ConfigurationError("No subjects defined in config/subjects.json")
    return [
        load_subject(subject_data, subject_name)
        for subject_name, subject_data in subjects.items()
    ]


def _load_note_type_rule(rule_name: str, rule_data: dict) -> NoteTypeRule:
    try:
        return NoteTypeRule(
            note_type=rule_data["note_type"],
            use_for=rule_data["use_for"],
            delimiter=rule_data.get("delimiter"),
            required_tag=rule_data.get("required_tag"),
            deck_suffix=rule_data.get("deck_suffix"),
            applies_to_subjects=rule_data.get("applies_to_subjects"),
            basic_qa_format=rule_data.get("basic_qa_format"),
        )
    except KeyError as error:
        raise ConfigurationError(
            f"Note type rule '{rule_name}' is missing required field: {error}"
        ) from error


def load_flashcard_preferences() -> FlashcardPreferences:
    data = _read_json(SETTINGS_PATH).get("flashcard_preferences", {})
    try:
        rules = {
            rule_name: _load_note_type_rule(rule_name, rule_data)
            for rule_name, rule_data in data.get("note_type_rules", {}).items()
        }
        return FlashcardPreferences(
            one_idea_per_card=data["one_idea_per_card"],
            exam_focused=data["exam_focused"],
            use_mark_scheme_terminology=data["use_mark_scheme_terminology"],
            concise=data["concise"],
            default_note_type=data["default_note_type"],
            note_type_rules=rules,
        )
    except KeyError as error:
        raise ConfigurationError(f"Missing flashcard preference: {error}") from error


def load_approval() -> ApprovalConfig:
    data = _read_json(SETTINGS_PATH).get("approval", {})
    return ApprovalConfig(
        required_for_anki_writes=data.get("required_for_anki_writes", True),
        allow_bulk_approve=data.get("allow_bulk_approve", True),
    )
