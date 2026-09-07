"""Tests for the configuration system (roadmap Phase 2)."""

import pytest

from src.config.loader import load_config, load_settings, load_subjects
from src.observability.errors import ConfigurationError


def test_load_config_returns_all_eleven_subjects():
    config = load_config()
    assert len(config.subjects) == 11


def test_chemistry_subject_details():
    config = load_config()
    chemistry = next(s for s in config.subjects if s.name == "chemistry")
    assert chemistry.exam_board == "CAIE"
    assert chemistry.qualification == "IGCSE"
    assert chemistry.syllabus_code == "0620"
    assert chemistry.anki_deck == "GCSE::Chemistry"


def test_flashcard_preferences_loaded():
    config = load_config()
    prefs = config.flashcard_preferences
    assert prefs.default_note_type == "Cloze"
    assert prefs.one_idea_per_card is True
    shuffle = prefs.note_type_rules["cloze_shuffle"]
    assert shuffle.delimiter == "||"
    assert shuffle.required_tag == "Shuffle"


def test_definitions_rule_targets_science_subjects():
    config = load_config()
    definitions = config.flashcard_preferences.note_type_rules["basic_and_extra"]
    assert "chemistry" in definitions.applies_to_subjects
    assert definitions.deck_suffix == "::Definitions"


def test_approval_gates_anki_writes():
    config = load_config()
    assert config.approval.required_for_anki_writes is True


def test_missing_config_file_raises_clean_error(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ConfigurationError):
        load_settings()
    with pytest.raises(ConfigurationError):
        load_subjects()
