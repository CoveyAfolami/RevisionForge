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
- [x] Phase 9–14 — LLM client (Groq/OpenRouter/Gemini/any), card generation, PDF extraction + chunking
- [x] Phase 21–22, 25 — Generation rules, deterministic validation, exact duplicate detection (batch + DB + Anki)
- [ ] Phases 27–32 — Approval CLI, safe execution, full pipeline, history

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
python -m src.app.main --preview book.pdf --subject chemistry --pages 140-146 --topic isotopes
                                          # generate cards and print them — NO Anki writes
```

### LLM providers

Set `LLM_PROVIDER` in `.env` — the client is OpenAI-compatible, so any of
these work without code changes:

| Provider | Free? | Key from |
|---|---|---|
| `groq` (default) | Yes, permanently | console.groq.com |
| `openrouter` | Free models available | openrouter.ai |
| `gemini` | Free tier | aistudio.google.com (18+) |
| `openai` | Paid | platform.openai.com |
| `ollama` | Free, local, offline | ollama.com (runs on your PC) |

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
