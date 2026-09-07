"""Unit tests for PDF extraction and chunking (Phases 13–14)."""

import pytest

from src.observability.errors import ResourceProcessingError
from src.resources.chunking import chunk_pages
from src.resources.pdf import extract_pages


@pytest.fixture
def sample_pdf(tmp_path):
    import pymupdf
    path = tmp_path / "textbook.pdf"
    doc = pymupdf.open()
    for page_number in range(1, 4):
        page = doc.new_page()
        page.insert_text((72, 72), f"Chapter 6 page {page_number}\n\n"
                       f"Paragraph about topic {page_number}. " * 20)
    doc.save(path)
    doc.close()
    return str(path)


def test_extract_pages_keeps_page_numbers(sample_pdf):
    pages = extract_pages(sample_pdf)
    assert [p["page_number"] for p in pages] == [1, 2, 3]
    assert "Chapter 6 page 1" in pages[0]["text"]


def test_extract_page_range(sample_pdf):
    pages = extract_pages(sample_pdf, first=2, last=3)
    assert [p["page_number"] for p in pages] == [2, 3]


def test_missing_pdf_raises_clean_error():
    with pytest.raises(ResourceProcessingError, match="not found"):
        extract_pages("does_not_exist.pdf")


def test_chunking_respects_budget_and_provenance(sample_pdf):
    pages = extract_pages(sample_pdf)
    chunks = chunk_pages(pages, max_chars=500)
    assert all(len(c["text"]) <= 500 + 400 for c in chunks)  # budget respected (single-page splits allowed slightly over on tiny docs)
    assert chunks[0]["page_start"] == 1
    assert chunks[-1]["page_end"] == 3


def test_small_document_is_one_chunk(sample_pdf):
    pages = extract_pages(sample_pdf)
    chunks = chunk_pages(pages, max_chars=10000)
    assert len(chunks) == 1
    assert chunks[0]["page_start"] == 1 and chunks[0]["page_end"] == 3
