# RevisionForge

A local tool that turns textbook chapters into exam-focused Anki flashcards.

Pipeline: textbook PDF → chapter extraction → syllabus-aware flashcard
generation (Gemini) → deterministic validation + duplicate detection →
your approval → safe Anki write with post-write verification.

## Status

- [x] Phase 1–2 — Application structure + configuration (11 subjects, card-style rules)
- [x] Phase 3 — Logging + custom exceptions
- [x] Phase 4 — SQLite layer (processing runs, resources, cards)
- [x] Phase 5 — AnkiConnect client (partial)
- [ ] Phases 6–8 — Full Anki read/write subsystem
- [ ] Phases 9–14 — LLM integration, card generation, PDF processing
- [ ] Phases 25–32 — Duplicates, approval, safe writes, history

Full plan: `docs/sources/revision-forge-implementation-architecture-and-roadmap.pdf`

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Mac/Linux
pip install -r requirements-dev.txt
cp .env.example .env         # then fill in your keys
```

Requires: Python 3.10+, Anki desktop running with the AnkiConnect add-on.

## Tests

```bash
pytest
```

## Design principles

- The syllabus is authoritative — resources serve it, never the reverse.
- Deterministic Python handles API calls, hashing, validation, and Anki writes.
  The LLM only reasons and writes card content.
- No Anki write without explicit approval; every write is verified after.
- Secrets live in `.env`, which is never committed.
