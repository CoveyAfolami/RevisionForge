"""Unit tests for the Anki subsystem (Phases 6–8) — fully offline.

The client is pointed at FakeAnkiConnect, so these run anywhere without
Anki installed. Live tests live in test_anki_integration.py.
"""

import pytest

from src.anki.client import AnkiConnectClient
from src.anki.mapper import AnkiMapper
from src.anki.models import NoteDraft, NoteInfo
from src.anki.verifier import verify_note
from src.config.loader import load_config
from src.observability.errors import AnkiConnectionError, ValidationError
from tests.fake_anki import FakeAnkiConnect

MODELS = {
    "Cloze": ["Text", "Extra"],
    "Cloze Shuffle": ["Text", "Extra"],
    "Basic (and extra)": ["Front", "Back", "Extra"],
    "Basic++": ["Front", "Back"],
}


@pytest.fixture
def fake():
    return FakeAnkiConnect(
        decks=["GCSE", "GCSE::Chemistry", "GCSE::Chemistry::Definitions"],
        models=MODELS,
    )


@pytest.fixture
def client(fake):
    return AnkiConnectClient(url="http://fake", key="test-key", transport=fake)


@pytest.fixture
def config():
    return load_config()


@pytest.fixture
def chemistry(config):
    return next(s for s in config.subjects if s.name == "chemistry")


def test_check_connection_sends_key(client, fake):
    assert client.check_connection() == 6
    assert fake.requests[0]["key"] == "test-key"


def test_unknown_note_type_raises_clean_error(client):
    with pytest.raises(AnkiConnectionError, match="not found"):
        client.get_note_type_fields("Nope")


def test_add_note_returns_id_and_rejects_duplicates(client):
    draft = NoteDraft(
        deck="GCSE::Chemistry", note_type="Cloze",
        fields={"Text": "What is {{c1::H2O}}?", "Extra": ""},
        tags=["CAIE", "IGCSE"],
    )
    note_id = client.add_note(draft.to_anki_payload())
    assert note_id is not None
    with pytest.raises(AnkiConnectionError, match="declined"):
        client.add_note(draft.to_anki_payload())


def test_note_info_parsed_from_anki_payload(client):
    draft = NoteDraft(deck="GCSE::Chemistry", note_type="Cloze",
                      fields={"Text": "T {{c1::x}}", "Extra": ""})
    note_id = client.add_note(draft.to_anki_payload())
    raw = client.get_notes_info([note_id])[0]
    info = NoteInfo.from_anki(raw)
    assert info.note_id == note_id
    assert info.deck == "GCSE::Chemistry"
    assert info.note_type == "Cloze"
    assert info.fields == {"Text": "T {{c1::x}}", "Extra": ""}


def test_mapper_sends_definitions_to_definitions_deck(client, config, chemistry):
    mapper = AnkiMapper(client, config)
    mapping = mapper.resolve(chemistry, card_kind="definition")
    assert mapping.deck == "GCSE::Chemistry::Definitions"
    assert mapping.note_type == "Basic (and extra)"
    assert mapping.deck_created is False
    assert set(mapping.field_names) == {"Front", "Back", "Extra"}


def test_mapper_history_definition_has_no_suffix(client, config):
    mapper = AnkiMapper(client, config)
    history = next(s for s in config.subjects if s.name == "history")
    mapping = mapper.resolve(history, card_kind="definition")
    # Definitions rule doesn't apply to history: plain deck, deck auto-created.
    assert mapping.deck == "GCSE::History"
    assert mapping.deck_created is True


def test_mapper_refuses_to_create_when_disabled(client, config):
    mapper = AnkiMapper(client, config)
    history = next(s for s in config.subjects if s.name == "history")
    with pytest.raises(ValidationError, match="does not exist"):
        mapper.resolve(history, card_kind="definition", create_missing_decks=False)


def test_mapper_rejects_unknown_card_kind(client, config, chemistry):
    mapper = AnkiMapper(client, config)
    with pytest.raises(ValidationError, match="Unknown card kind"):
        mapper.resolve(chemistry, card_kind="meme")


def test_build_fields_cloze_vs_basic(client, config, chemistry):
    mapper = AnkiMapper(client, config)

    cloze = mapper.resolve(chemistry, card_kind="cloze")
    fields = mapper.build_fields(cloze, front="Q {{c1::answer}}", back="")
    assert fields == {"Text": "Q {{c1::answer}}", "Extra": ""}

    qa = mapper.resolve(chemistry, card_kind="qa")
    # Basic++ has no Extra field, so extra content is correctly dropped.
    fields = mapper.build_fields(qa, front="Q", back="A", extra="context")
    assert fields == {"Front": "Q", "Back": "A"}


def test_find_notes_by_deck_and_text(client):
    draft = NoteDraft(deck="GCSE::Chemistry", note_type="Cloze",
                      fields={"Text": "isotopes have different neutrons", "Extra": ""})
    client.add_note(draft.to_anki_payload())
    ids = client.find_notes('deck:"GCSE::Chemistry" isotope')
    assert len(ids) == 1


def test_verify_note_passes_on_good_write(client):
    draft = NoteDraft(deck="GCSE::Chemistry", note_type="Cloze",
                      fields={"Text": "Verify {{c1::me}}", "Extra": ""},
                      tags=["test"])
    note_id = client.add_note(draft.to_anki_payload())
    result = verify_note(client, note_id, draft)
    assert result.ok, result.issues


def test_verify_note_flags_wrong_deck_and_field(client):
    draft = NoteDraft(deck="GCSE::Chemistry", note_type="Cloze",
                      fields={"Text": "V {{c1::x}}", "Extra": ""})
    note_id = client.add_note(draft.to_anki_payload())

    wrong = NoteDraft(deck="GCSE::Biology", note_type="Cloze",
                      fields={"Text": "V {{c1::CHANGED}}", "Extra": ""})
    result = verify_note(client, note_id, wrong)
    assert not result.ok
    assert any("deck" in issue for issue in result.issues)
    assert any("field" in issue for issue in result.issues)
