"""Post-write verification (roadmap Phase 31).

Never trust a success code. After any write, fetch the note back from
Anki and compare it against what we intended to create.
"""

from .client import AnkiConnectClient
from .models import NoteDraft, VerifyResult


def verify_note(client: AnkiConnectClient, note_id: int,
                expected: NoteDraft) -> VerifyResult:
    """Fetch the created note and compare deck, type, fields, and tags."""
    infos = client.get_notes_info([note_id])
    if not infos:
        return VerifyResult(False, [f"Note {note_id} not found after write"])

    raw = infos[0]
    issues = []

    actual_deck = (raw.get("cards") or [{}])[0].get("deckName", "")
    if actual_deck != expected.deck:
        issues.append(f"deck: expected '{expected.deck}', got '{actual_deck}'")

    actual_type = raw.get("modelName", "")
    if actual_type != expected.note_type:
        issues.append(f"note type: expected '{expected.note_type}', got '{actual_type}'")

    actual_fields = {
        name: data.get("value", "")
        for name, data in raw.get("fields", {}).items()
    }
    for name, value in expected.fields.items():
        if actual_fields.get(name) != value:
            issues.append(
                f"field '{name}': expected {value!r}, got {actual_fields.get(name)!r}"
            )

    actual_tags = set(raw.get("tags", []))
    missing_tags = set(expected.tags) - actual_tags
    if missing_tags:
        issues.append(f"tags: missing {sorted(missing_tags)}")

    return VerifyResult(ok=not issues, issues=issues)
