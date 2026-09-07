"""PDF text extraction (roadmap Phase 13) — text-based PDFs first, OCR later.

Every extracted page keeps its page number so cards can always be traced
back to their exact source pages.
"""

from pathlib import Path

from ..observability.errors import ResourceProcessingError


def extract_pages(pdf_path: str, first: int | None = None,
                  last: int | None = None) -> list[dict]:
    """Extract text per page, optionally restricted to a page range (1-based)."""
    path = Path(pdf_path)
    if not path.exists():
        raise ResourceProcessingError(f"PDF not found: {pdf_path}")

    try:
        import pymupdf
    except ImportError as error:
        raise ResourceProcessingError(
            "pymupdf is not installed — run: pip install -r requirements-dev.txt"
        ) from error

    try:
        doc = pymupdf.open(path)
        start = max((first or 1) - 1, 0)
        end = min(last or doc.page_count, doc.page_count)
        pages = [
            {"page_number": number + 1, "text": doc[number].get_text("text")}
            for number in range(start, end)
        ]
        doc.close()
    except Exception as error:
        raise ResourceProcessingError(f"Could not read PDF {pdf_path}: {error}") from error

    if not any(page["text"].strip() for page in pages):
        raise ResourceProcessingError(
            "No extractable text found — this may be a scanned PDF "
            "(OCR support comes later)"
        )
    return pages
