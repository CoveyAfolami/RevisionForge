"""FlashcardDraft — the pipeline's card schema (roadmap Phase 10).

Raw LLM JSON is parsed into this dataclass at the boundary and anything
malformed is rejected immediately. Nothing unvalidated ever moves forward.
"""

from dataclasses import dataclass, field

from ..observability.errors import ValidationError

VALID_KINDS = {"cloze", "shuffle", "definition", "qa"}


@dataclass
class FlashcardDraft:
    card_kind: str
    front: str
    back: str
    extra: str = ""
    topic: str = ""
    tags: list[str] = field(default_factory=list)

    @classmethod
    def from_llm(cls, data: dict) -> "FlashcardDraft":
        """Parse one card from LLM output; raises ValidationError if malformed."""
        if not isinstance(data, dict):
            raise ValidationError(f"Card entry is not a JSON object: {data!r}")

        kind = str(data.get("card_kind", "cloze")).lower().strip()
        if kind not in VALID_KINDS:
            raise ValidationError(f"Unknown card kind from LLM: {kind!r}")

        front = str(data.get("front") or "").strip()
        if not front:
            raise ValidationError("Card is missing front text")

        back = str(data.get("back") or "").strip()
        extra = str(data.get("extra") or "").strip()
        topic = str(data.get("topic") or "").strip()

        raw_tags = data.get("tags") or []
        if not isinstance(raw_tags, list):
            raise ValidationError(f"Card tags must be a list, got: {raw_tags!r}")
        tags = [str(t).strip() for t in raw_tags if str(t).strip()]

        return cls(card_kind=kind, front=front, back=back, extra=extra,
                   topic=topic, tags=tags)
