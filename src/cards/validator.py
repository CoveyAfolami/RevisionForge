"""Deterministic card validation (roadmap Phase 22).

Normal Python checks, no LLM: malformed cards are rejected before they can
reach quality control or Anki. Every check is a rule, not an opinion.
"""

from .models import FlashcardDraft

MAX_FRONT_CHARS = 500
MAX_BACK_CHARS = 1000


def validate_card(card: FlashcardDraft) -> list[str]:
    """Return a list of issues; empty list means the card is valid."""
    issues: list[str] = []

    if not card.front:
        issues.append("empty front")
    if len(card.front) > MAX_FRONT_CHARS:
        issues.append(f"front too long ({len(card.front)} > {MAX_FRONT_CHARS} chars)")
    if len(card.back) > MAX_BACK_CHARS:
        issues.append(f"back too long ({len(card.back)} > {MAX_BACK_CHARS} chars)")

    if card.card_kind == "cloze":
        if "{{c1::" not in card.front:
            issues.append("cloze card missing a {{c1::...}} deletion")
    elif card.card_kind == "shuffle":
        if "||" not in card.front:
            issues.append("shuffle card missing '||' delimiters between items")
        if "{{c1::" not in card.front:
            issues.append("shuffle card missing cloze deletions")
    elif card.card_kind == "definition":
        if not card.back:
            issues.append("definition card missing back (mark-scheme answer)")
    elif card.card_kind == "qa":
        if not card.back:
            issues.append("Q&A card missing back (answer)")

    return issues


def validate_cards(cards: list[FlashcardDraft]):
    """Split a batch into (valid, rejected) where rejected = (card, issues)."""
    valid, rejected = [], []
    for card in cards:
        issues = validate_card(card)
        if issues:
            rejected.append((card, issues))
        else:
            valid.append(card)
    return valid, rejected
