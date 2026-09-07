"""Live integration tests against a running Anki + AnkiConnect.

Run on YOUR machine with Anki desktop open:
    pytest tests/test_anki_integration.py -v

These auto-skip when AnkiConnect is unreachable, so a plain `pytest`
anywhere else still passes. All writes are confined to the
'AI Agent Test' deck and cleaned up afterwards.
"""

import pytest

from src.anki.client import AnkiConnectClient
from src.anki.mapper import AnkiMapper
from src.anki.models import NoteDraft
from src.anki.verifier import verify_note
from src.config.loader import load_config

TEST_DECK = "AI Agent Test"


def _is_reachable() -> bool:
    try:
        AnkiConnectClient(timeout=3).check_connection()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _is_reachable(), reason="AnkiConnect not reachable")


@pytest.fixture
def client():
    return AnkiConnectClient()


def test_connection_and_structure(client):
    version = client.check_connection()
    assert version >= 6
    assert "GCSE" in client.get_decks()
    assert "Cloze" in client.get_note_types()


def test_real_note_type_fields_are_inspectable(client):
    fields = client.get_note_type_fields("Cloze")
    assert "Text" in fields


def test_full_write_cycle_to_test_deck(client):
    client.create_deck(TEST_DECK)
    draft = NoteDraft(
        deck=TEST_DECK,
        note_type="Cloze",
        fields={"Text": "RevisionForge verification {{c1::works}}", "Extra": ""},
        tags=["revision-forge", "test"],
    )
    note_id = client.add_note(draft.to_anki_payload())

    result = verify_note(client, note_id, draft)
    assert result.ok, result.issues

    # Duplicate must be refused.
    with pytest.raises(Exception, match="declined"):
        client.add_note(draft.to_anki_payload())

    # Cleanup: leave the test deck empty.
    client.delete_notes([note_id])
    assert client.find_notes(f'deck:"{TEST_DECK}" tag:revision-forge') == []


def test_mapper_against_real_anki(client):
    config = load_config()
    mapper = AnkiMapper(client, config)
    chemistry = next(s for s in config.subjects if s.name == "chemistry")
    # Preview mode: no decks get created.
    mapping = mapper.resolve(chemistry, card_kind="cloze", create_missing_decks=False)
    assert mapping.deck == "GCSE::Chemistry"
    assert "Text" in mapping.field_names
