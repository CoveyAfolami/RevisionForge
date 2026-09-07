"""Exact duplicate detection (roadmap Phase 25) — deterministic, no LLM.

Three layers: within the current batch, against previous runs (SQLite),
and against what already exists in Anki. Related-but-different cards are
NOT duplicates — semantic detection is deliberately a later phase.
"""

import re

from .hashing import hash_card
from .models import FlashcardDraft


def strip_cloze(text: str) -> str:
    """Remove cloze markup so duplicate text comparisons see the plain text."""
    return re.sub(r"\{\{c\d+::(.*?)\}\}", r"\1", text)


def _anki_query_text(front: str) -> str:
    """A short, quote-free fragment of the front to search Anki with."""
    plain = strip_cloze(front).replace('"', "'").strip()
    return plain[:60]


def find_duplicates(cards: list[FlashcardDraft], cards_repo=None,
                    anki_client=None, deck: str | None = None):
    """Returns (unique_cards, duplicates) where duplicates = (card, reason)."""
    unique, duplicates = [], []
    seen_hashes: dict[str, int] = {}

    for card in cards:
        content_hash = hash_card(card.front, card.back or card.extra or "")
        reason = None

        if content_hash in seen_hashes:
            reason = f"in-batch duplicate of card #{seen_hashes[content_hash]}"
        elif cards_repo is not None and cards_repo.find_by_content_hash(content_hash):
            reason = "already generated in a previous run (database)"
        elif anki_client is not None and deck:
            needle = _anki_query_text(card.front)
            if needle:
                try:
                    hits = anki_client.find_notes(f'deck:"{deck}" "{needle}"')
                    if hits:
                        reason = f"already in Anki ({len(hits)} matching notes)"
                except Exception:
                    pass  # Anki not running: skip the Anki layer, stay deterministic

        if reason:
            duplicates.append((card, reason))
        else:
            seen_hashes[content_hash] = len(unique) + 1
            unique.append(card)

    return unique, duplicates
