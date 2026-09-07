"""Decides where a card belongs in Anki (roadmap Phase 8).

Critical rule: field names are NEVER assumed — the real note type is
inspected through AnkiConnect every time. "Cloze" types use Text/Extra;
basic types use Front/Back/Extra; anything unexpected fails loudly.
"""

from ..config.models import AppConfig, SubjectConfig
from ..observability.errors import AnkiConnectionError, ValidationError
from .client import AnkiConnectClient
from .models import NoteMapping

# card_kind -> key into config flashcard_preferences.note_type_rules
KIND_TO_RULE = {
    "cloze": "cloze",
    "shuffle": "cloze_shuffle",
    "definition": "basic_and_extra",
    "qa": "basic_pp",
}


class AnkiMapper:
    def __init__(self, client: AnkiConnectClient, config: AppConfig):
        self.client = client
        self.config = config

    def resolve(self, subject: SubjectConfig, card_kind: str = "cloze",
                note_type: str | None = None,
                create_missing_decks: bool = True) -> NoteMapping:
        """Resolve deck + note type + real field names for a card."""
        if card_kind not in KIND_TO_RULE:
            raise ValidationError(f"Unknown card kind: {card_kind}")

        prefs = self.config.flashcard_preferences
        rule = prefs.note_type_rules[KIND_TO_RULE[card_kind]]
        resolved_note_type = note_type or rule.note_type

        # Deck: subject deck, with the definitions sub-deck convention.
        deck = subject.anki_deck
        if card_kind == "definition" and rule.deck_suffix:
            applies = rule.applies_to_subjects
            if applies is None or subject.name in applies:
                deck = deck + rule.deck_suffix

        # Inspect the real note type — never assume its fields.
        try:
            field_names = self.client.get_note_type_fields(resolved_note_type)
        except AnkiConnectionError as error:
            raise ValidationError(
                f"Note type '{resolved_note_type}' not found in Anki — "
                f"create it first. ({error})"
            ) from error

        # Deck existence: create on demand, but say so.
        deck_created = False
        if deck not in self.client.get_decks():
            if not create_missing_decks:
                raise ValidationError(f"Deck '{deck}' does not exist in Anki")
            self.client.create_deck(deck)
            deck_created = True

        return NoteMapping(
            deck=deck,
            note_type=resolved_note_type,
            field_names=field_names,
            deck_created=deck_created,
        )

    def build_fields(self, mapping: NoteMapping, front: str, back: str = "",
                     extra: str | None = None) -> dict[str, str]:
        """Translate pipeline card content into the note type's real fields."""
        is_cloze = "cloze" in mapping.note_type.lower()
        fields: dict[str, str] = {}

        if is_cloze:
            if "Text" not in mapping.field_names:
                raise ValidationError(
                    f"Note type '{mapping.note_type}' has no Text field"
                )
            fields["Text"] = front
            if "Extra" in mapping.field_names:
                fields["Extra"] = extra if extra is not None else back
        else:
            if "Front" not in mapping.field_names or "Back" not in mapping.field_names:
                raise ValidationError(
                    f"Note type '{mapping.note_type}' lacks Front/Back fields: "
                    f"{mapping.field_names}"
                )
            fields["Front"] = front
            fields["Back"] = back
            if extra is not None and "Extra" in mapping.field_names:
                fields["Extra"] = extra

        return fields
