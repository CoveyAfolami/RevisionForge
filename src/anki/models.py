"""Typed representations of Anki objects.

Raw dicts from AnkiConnect never flow through the application — they are
parsed into these dataclasses at the boundary, so the rest of the code
works with known shapes.
"""

from dataclasses import dataclass, field


@dataclass
class NoteDraft:
    """A note ready to be added to Anki."""
    deck: str
    note_type: str
    fields: dict[str, str]
    tags: list[str] = field(default_factory=list)

    def to_anki_payload(self) -> dict:
        """The exact JSON AnkiConnect expects for addNotes."""
        return {
            "deckName": self.deck,
            "modelName": self.note_type,
            "fields": self.fields,
            "tags": self.tags,
            "options": {"allowDuplicate": False},
        }


@dataclass
class NoteInfo:
    """A note as it actually exists in Anki right now."""
    note_id: int
    deck: str
    note_type: str
    fields: dict[str, str]
    tags: list[str]

    @classmethod
    def from_anki(cls, raw: dict) -> "NoteInfo":
        fields = {
            name: data.get("value", "")
            for name, data in raw.get("fields", {}).items()
        }
        cards = raw.get("cards", [])
        deck = cards[0]["deckName"] if cards else ""
        return cls(
            note_id=raw["noteId"],
            deck=deck,
            note_type=raw.get("modelName", ""),
            fields=fields,
            tags=raw.get("tags", []),
        )


@dataclass
class NoteMapping:
    """Where a card belongs: resolved deck, note type, and the real fields."""
    deck: str
    note_type: str
    field_names: list[str]
    deck_created: bool = False


@dataclass
class VerifyResult:
    """Outcome of a post-write verification."""
    ok: bool
    issues: list[str] = field(default_factory=list)
