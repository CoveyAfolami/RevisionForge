"""Card generation: source chunks in, FlashcardDrafts out (Phase 21).

The LLM proposes; Python validates. Malformed cards are collected as
errors and never enter the pipeline.
"""

from ..agent.llm_client import LLMClient
from ..agent.prompts import CARD_SYSTEM_PROMPT, build_user_prompt
from ..config.models import AppConfig, SubjectConfig
from ..observability.errors import ValidationError
from ..observability.logging import get_logger
from .models import FlashcardDraft

logger = get_logger("generator")


class CardGenerator:
    def __init__(self, llm: LLMClient, config: AppConfig):
        self.llm = llm
        self.config = config

    def generate(self, subject: SubjectConfig, chunks: list[dict],
                 topic_hint: str | None = None):
        """Returns (cards, errors): parsed, tag-augmented drafts + LLM issues."""
        cards: list[FlashcardDraft] = []
        errors: list[str] = []

        for chunk in chunks:
            result = self.llm.generate_structured(
                CARD_SYSTEM_PROMPT, build_user_prompt(subject, chunk, topic_hint)
            )
            batch = result.get("cards", []) if isinstance(result, dict) else []
            parsed = 0
            for item in batch:
                try:
                    cards.append(FlashcardDraft.from_llm(item))
                    parsed += 1
                except ValidationError as error:
                    errors.append(f"Rejected malformed card: {error}")
            logger.info("Chunk pages %s-%s: %d cards parsed, %d malformed",
                        chunk["page_start"], chunk["page_end"],
                        parsed, len(batch) - parsed)

        return self._augment_tags(cards, subject), errors

    @staticmethod
    def _augment_tags(cards, subject: SubjectConfig):
        """Add board / qualification / subject / topic tags to every card."""
        for card in cards:
            base = [subject.exam_board, subject.qualification,
                    subject.name.replace("_", " ").title()]
            if card.topic:
                base.append(card.topic.replace(" ", "_"))
            merged, seen = [], set()
            for tag in card.tags + base:
                if tag not in seen:
                    seen.add(tag)
                    merged.append(tag)
            card.tags = merged
        return cards
