"""Chunking (roadmap Phase 14): keep provenance, control size.

Large textbooks can't be dumped into the model whole. Pages are grouped
into chunks that respect a character budget, and every chunk remembers
exactly which pages it came from — so a card can always cite its source.
"""

MAX_CHUNK_CHARS = 3500


def chunk_pages(pages: list[dict], max_chars: int = MAX_CHUNK_CHARS) -> list[dict]:
    """Group extracted pages into LLM-sized chunks with page provenance."""
    if not pages:
        return []

    chunks: list[dict] = []
    buffer: list[dict] = []  # holds {"page_number", "text"} pieces
    buffer_chars = 0

    def flush():
        nonlocal buffer, buffer_chars
        if buffer:
            chunks.append({
                "page_start": buffer[0]["page_number"],
                "page_end": buffer[-1]["page_number"],
                "text": "\n\n".join(piece["text"] for piece in buffer),
            })
        buffer, buffer_chars = [], 0

    for page in pages:
        for piece in _split_long_text(page["text"], max_chars):
            if buffer and buffer_chars + len(piece) > max_chars:
                flush()
            buffer.append({"page_number": page["page_number"], "text": piece})
            buffer_chars += len(piece)
    flush()

    return chunks


def _split_long_text(text: str, max_chars: int) -> list[str]:
    """Split a single oversized page on paragraph boundaries."""
    if len(text) <= max_chars:
        return [text]
    pieces, current = [], ""
    for paragraph in text.split("\n\n"):
        candidate = f"{current}\n\n{paragraph}".strip()
        if len(candidate) > max_chars and current:
            pieces.append(current)
            current = paragraph
        else:
            current = candidate
    if current:
        pieces.append(current)
    return pieces
