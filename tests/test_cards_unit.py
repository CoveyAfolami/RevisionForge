"""Unit tests for the LLM client + card pipeline (Phases 9, 10, 21, 22, 25).

All offline: the LLM transport is faked, so these run without any API key.
"""

import pytest

from src.agent.llm_client import LLMClient
from src.cards.duplicates import find_duplicates, strip_cloze
from src.cards.generator import CardGenerator
from src.cards.models import FlashcardDraft
from src.cards.validator import validate_card, validate_cards
from src.config.loader import load_config
from src.database.connection import connect
from src.database.repositories.cards import CardRepository
from src.database.repositories.runs import ProcessingRunRepository
from src.observability.errors import ConfigurationError, ValidationError


class FakeLLM:
    """Stands in for Groq/OpenRouter: returns canned completions."""

    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []

    def __call__(self, url, json=None, headers=None, timeout=None):
        self.calls.append({"url": url, "json": json, "headers": headers})
        content = self.replies.pop(0)
        return _LLMResponse(content)


class _LLMResponse:
    def __init__(self, content, status_code=200):
        self._content = content
        self.status_code = status_code

    def json(self):
        if self.status_code != 200:
            return {"error": {"message": self._content}}
        return {"choices": [{"message": {"content": self._content}}]}


def make_client(fake):
    return LLMClient(provider="groq", api_key="test-key", transport=fake)


# ---- LLM client ----

def test_structured_output_parses_even_with_markdown_fences():
    fake = FakeLLM(['```json\n{"cards": [{"front": "{{c1::x}}"}]}\n```'])
    result = make_client(fake).generate_structured("sys", "user")
    assert result["cards"][0]["front"] == "{{c1::x}}"
    assert "api.groq.com" in fake.calls[0]["url"]
    assert fake.calls[0]["headers"]["Authorization"] == "Bearer test-key"


def test_invalid_json_is_retried_then_fails_loudly():
    fake = FakeLLM(["not json at all", "still not json"])
    with pytest.raises(ValidationError, match="valid JSON"):
        make_client(fake).generate_structured("sys", "user")
    assert len(fake.calls) == 2  # both attempts used


def test_retry_recovers_after_one_bad_response():
    fake = FakeLLM(["oops not json", '{"cards": []}'])
    result = make_client(fake).generate_structured("sys", "user")
    assert result == {"cards": []}


def test_missing_provider_key_is_a_clean_configuration_error(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(ConfigurationError, match="GROQ_API_KEY"):
        LLMClient(provider="groq", api_key="")


def test_unknown_provider_is_rejected():
    with pytest.raises(ConfigurationError, match="Unknown LLM_PROVIDER"):
        LLMClient(provider="skynet", api_key="x")


# ---- FlashcardDraft schema ----

def test_from_llm_accepts_valid_card():
    card = FlashcardDraft.from_llm({
        "card_kind": "shuffle",
        "front": "{{c1::A}} || {{c2::B}} || {{c3::C}} || {{c4::D}}",
        "back": "", "extra": "", "topic": "list", "tags": ["Shuffle"],
    })
    assert card.card_kind == "shuffle"
    assert "Shuffle" in card.tags


def test_from_llm_rejects_unknown_kind_and_empty_front():
    with pytest.raises(ValidationError, match="Unknown card kind"):
        FlashcardDraft.from_llm({"card_kind": "meme", "front": "x"})
    with pytest.raises(ValidationError, match="missing front"):
        FlashcardDraft.from_llm({"card_kind": "cloze", "front": ""})


# ---- Validator ----

def test_validator_catches_each_broken_kind():
    assert "missing a {{c1::" in " ".join(validate_card(
        FlashcardDraft(card_kind="cloze", front="No deletion here", back="")))
    assert "missing '||'" in " ".join(validate_card(
        FlashcardDraft(card_kind="shuffle", front="{{c1::only}}", back="")))
    assert "missing back" in " ".join(validate_card(
        FlashcardDraft(card_kind="definition", front="Define isotope", back="")))
    assert not validate_card(FlashcardDraft(
        card_kind="cloze", front="What is {{c1::H2O}}?", back=""))


def test_validate_cards_splits_good_from_bad():
    cards = [
        FlashcardDraft(card_kind="cloze", front="Q {{c1::ok}}", back=""),
        FlashcardDraft(card_kind="cloze", front="broken", back=""),
    ]
    valid, rejected = validate_cards(cards)
    assert len(valid) == 1 and len(rejected) == 1


# ---- Generator ----

GOOD_BATCH = """{"cards": [
    {"card_kind": "cloze", "front": "What is {{c1::an isotope}}?", "back": "",
     "extra": "", "topic": "isotopes", "tags": []},
    {"card_kind": "shuffle", "front": "{{c1::A}} || {{c2::B}} || {{c3::C}} || {{c4::D}}",
     "back": "", "extra": "", "topic": "list", "tags": ["Shuffle"]},
    {"card_kind": "bogus", "front": "???", "back": ""}
]}"""


def test_generator_parses_augments_tags_and_collects_errors():
    config = load_config()
    fake = FakeLLM([GOOD_BATCH])
    generator = CardGenerator(make_client(fake), config)
    chemistry = next(s for s in config.subjects if s.name == "chemistry")
    chunks = [{"page_start": 140, "page_end": 146, "text": "Isotopes are..."}]

    cards, errors = generator.generate(chemistry, chunks, topic_hint="isotopes")

    assert len(cards) == 2 and len(errors) == 1
    assert cards[0].tags[:3] == ["CAIE", "IGCSE", "Chemistry"]
    assert "isotopes" in cards[0].tags
    assert "pages 140-146" in fake.calls[0]["json"]["messages"][1]["content"]


# ---- Duplicate detection ----

def _isotope_card():
    return FlashcardDraft(
        card_kind="cloze",
        front="What is {{c1::an isotope}}?",
        back="Atoms of the same element with different neutron counts",
        topic="isotopes",
    )


def test_in_batch_duplicates_are_detected():
    unique, duplicates = find_duplicates([_isotope_card(), _isotope_card()])
    assert len(unique) == 1 and len(duplicates) == 1
    assert "in-batch" in duplicates[0][1]


def test_database_duplicates_are_detected(tmp_path):
    db = connect(str(tmp_path / "test.db"))
    runs, cards_repo = ProcessingRunRepository(db), CardRepository(db)
    run_id = runs.create(subject="chemistry")
    original = _isotope_card()
    cards_repo.create(run_id, "chemistry", original.front, original.back, "Cloze")

    unique, duplicates = find_duplicates([_isotope_card()], cards_repo=cards_repo)
    assert len(unique) == 0 and "database" in duplicates[0][1]


def test_anki_duplicates_are_detected():
    from src.anki.client import AnkiConnectClient
    from tests.fake_anki import FakeAnkiConnect

    fake_anki = FakeAnkiConnect(
        decks=["GCSE::Chemistry"],
        models={"Cloze": ["Text", "Extra"]},
    )
    client = AnkiConnectClient(url="http://fake", transport=fake_anki)
    client.add_note({"deckName": "GCSE::Chemistry", "modelName": "Cloze",
                     "fields": {"Text": "What is an isotope?", "Extra": ""},
                     "tags": [], "options": {"allowDuplicate": False}})

    unique, duplicates = find_duplicates([_isotope_card()], anki_client=client,
                                        deck="GCSE::Chemistry")
    assert len(unique) == 0 and "Anki" in duplicates[0][1]


def test_strip_cloze_removes_markup():
    assert strip_cloze("{{c1::answer}} stays") == "answer stays"


def test_related_but_different_cards_are_not_duplicates():
    from src.cards.hashing import hash_card
    assert hash_card("What is an isotope?", "same element, different neutrons") != \
           hash_card("Define an isotope.", "atoms with different neutron counts")
