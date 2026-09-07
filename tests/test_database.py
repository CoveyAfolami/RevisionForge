"""Tests for the database layer (roadmap Phase 4)."""

import pytest

from src.cards.hashing import hash_card
from src.database.connection import connect
from src.database.repositories.cards import CardRepository
from src.database.repositories.resources import ResourceRepository
from src.database.repositories.runs import ProcessingRunRepository


@pytest.fixture
def db(tmp_path):
    return connect(str(tmp_path / "test.db"))


def test_processing_run_lifecycle(db):
    runs = ProcessingRunRepository(db)
    run_id = runs.create(user_request="Process Chapter 6", subject="chemistry")
    assert runs.get(run_id)["status"] == "running"
    runs.complete(run_id, cards_generated=10, cards_approved=8, cards_added=8)
    finished = runs.get(run_id)
    assert finished["status"] == "completed"
    assert finished["cards_generated"] == 10


def test_processing_run_failure_is_recorded(db):
    runs = ProcessingRunRepository(db)
    run_id = runs.create(subject="chemistry")
    runs.fail(run_id, "Anki not running")
    assert runs.get(run_id)["status"] == "failed"
    assert "Anki not running" in runs.get(run_id)["error_message"]


def test_resource_file_hash_prevents_reprocessing(db, tmp_path):
    resources = ResourceRepository(db)
    pdf = tmp_path / "chapter6.pdf"
    pdf.write_bytes(b"fake pdf content")
    file_hash = ResourceRepository.hash_file(pdf)

    resources.create(str(pdf), pdf.name, file_hash, subject="chemistry")
    assert resources.find_by_hash(file_hash) is not None


def test_card_exact_duplicate_detection_via_hash(db):
    runs = ProcessingRunRepository(db)
    run_id = runs.create(subject="chemistry")
    cards = CardRepository(db)

    front, back = "What is an isotope?", "Atoms of the same element with different numbers of neutrons"
    card_id = cards.create(run_id, "chemistry", front, back, "Basic++")
    stored_hash = cards.get(card_id)["content_hash"]

    # Same content with different casing/whitespace must produce the same hash.
    rephrased = hash_card("what IS an  isotope?  ", back.upper())
    assert rephrased == stored_hash
    assert cards.find_by_content_hash(rephrased) is not None


def test_card_status_tracks_anki_write(db):
    runs = ProcessingRunRepository(db)
    run_id = runs.create(subject="chemistry")
    cards = CardRepository(db)
    card_id = cards.create(run_id, "chemistry", "Q", "A", "Cloze")

    cards.update_status(card_id, "approved")
    assert cards.get(card_id)["status"] == "approved"

    cards.update_status(card_id, "written", anki_note_id=123456789)
    written = cards.get(card_id)
    assert written["status"] == "written"
    assert written["anki_note_id"] == 123456789
