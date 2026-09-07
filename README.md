# RevisionForge

A local tool that turns textbook chapters into exam-focused Anki flashcards.

Pipeline: textbook PDF → chapter extraction → syllabus-aware flashcard
generation (Gemini) → deterministic validation + duplicate detection →
your approval → safe Anki write with post-write verification.

## Status

- [x] Phase 1–2 — Application structure + configuration (11 subjects, card-style rules)
- [x] Phase 3 — Logging + custom exceptions
- [x] Phase 4 — SQLite layer (processing runs, resources, cards)
- [x] Phase 5–8 — AnkiConnect client, full reads, safe writes, deck/note-type mapping, post-write verification
- [ ] Phases 9–14 — LLM integration, card generation, PDF processing
- [ ] Phases 25–32 — Duplicates, approval CLI, full pipeline, history

Full plan: `docs/sources/revision-forge-implementation-architecture-and-roadmap.pdf`

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Mac/Linux
pip install -r requirements-dev.txt
cp .env.example .env         # then fill in your keys
```

Requires: Python 3.10+, Anki desktop with the AnkiConnect add-on (for live use).

## Usage

```bash
python -m src.app.main --anki-check       # is Anki reachable? list decks + note types
python -m src.app.main --fields Cloze     # show real field names of a note type
python -m src.app.main --map chemistry    # where each card kind goes for a subject
```

## Tests

```bash
pytest                                     # everything (live tests auto-skip)
pytest tests/test_anki_integration.py -v   # live Anki tests — run with Anki open
```

Unit tests run fully offline against a fake AnkiConnect (`tests/fake_anki.py`).

## Design principles

- The syllabus is authoritative — resources serve it, never the reverse.
- Deterministic Python handles API calls, hashing, validation, and Anki writes.
  The LLM only reasons and writes card content.
- Field names are never assumed — real note types are inspected every time.
- No Anki write without explicit approval; every write is verified after by
  fetching the note back and comparing it.
- Secrets live in `.env` (uppercase names), which is never committed.
