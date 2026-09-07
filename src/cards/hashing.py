"""Text normalisation and content hashing for duplicate detection.

Deterministic (no LLM): two cards count as exact duplicates when their
normalised front + back text hash to the same value.
"""

import hashlib
import re


def normalize_text(text: str) -> str:
    """Lowercase, collapse whitespace, and trim — so trivially different
    phrasings of the same content hash identically."""
    return re.sub(r"\s+", " ", text.strip().lower())


def hash_card(front: str, back: str) -> str:
    """SHA-256 of the normalised front + back. Cards are compared by value,
    never by id, so a re-generated identical card is still caught."""
    combined = f"{normalize_text(front)}::{normalize_text(back)}"
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()
