"""RevisionForge command-line entry point.

Usage:
    python -m src.app.main --anki-check          # connection + decks + note types
    python -m src.app.main --fields Cloze        # real fields of a note type
    python -m src.app.main --map chemistry       # where cards go for a subject
    python -m src.app.main --preview book.pdf --subject chemistry --pages 140-146
                                                 # generate cards, print, NO Anki writes
"""

import argparse

from ..agent.llm_client import LLMClient
from ..anki.client import AnkiConnectClient
from ..anki.mapper import AnkiMapper
from ..cards.duplicates import find_duplicates
from ..cards.generator import CardGenerator
from ..cards.validator import validate_cards
from ..config.loader import load_config
from ..observability.errors import AnkiConnectionError
from ..observability.logging import configure_logging
from ..resources.chunking import chunk_pages
from ..resources.pdf import extract_pages


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="revisionforge",
        description="Turn textbooks into exam-focused Anki flashcards.",
    )
    parser.add_argument("--anki-check", action="store_true",
                        help="test the AnkiConnect connection and list decks/note types")
    parser.add_argument("--fields", metavar="NOTE_TYPE",
                        help="show the field names of a note type")
    parser.add_argument("--map", metavar="SUBJECT",
                        help="show where each card kind would go for a subject")
    parser.add_argument("--preview", metavar="PDF",
                        help="generate cards from a PDF and print them (no Anki writes)")
    parser.add_argument("--subject", default="chemistry",
                        help="subject key from config/subjects.json (default: chemistry)")
    parser.add_argument("--pages", metavar="FIRST-LAST",
                        help="page range to process, e.g. 140-146")
    parser.add_argument("--topic", help="topic hint for generation, e.g. 'isotopes'")
    args = parser.parse_args(argv)

    config = load_config()
    configure_logging(config.settings.log_level, config.settings.log_file)
    subjects = {s.name: s for s in config.subjects}

    if not any(value for key, value in vars(args).items() if key != "subject"):
        parser.print_help()
        return

    if args.anki_check:
        client = AnkiConnectClient()
        version = client.check_connection()
        print(f"AnkiConnect is live (API version {version})")
        print("Decks: " + ", ".join(client.get_decks()))
        print("Note types: " + ", ".join(client.get_note_types()))

    if args.fields:
        client = AnkiConnectClient()
        fields = client.get_note_type_fields(args.fields)
        print(f"{args.fields} fields: " + ", ".join(fields))

    if args.map:
        if args.map not in subjects:
            print(f"Unknown subject '{args.map}'. Known: {', '.join(subjects)}")
            return
        # Preview only: never create decks just by looking.
        mapper = AnkiMapper(AnkiConnectClient(), config)
        for kind in ("cloze", "shuffle", "definition", "qa"):
            try:
                mapping = mapper.resolve(subjects[args.map], card_kind=kind,
                                         create_missing_decks=False)
                print(f"{kind:11} -> {mapping.deck}  [{mapping.note_type}] "
                      f"({', '.join(mapping.field_names)})")
            except Exception as error:
                print(f"{kind:11} -> unavailable ({error})")

    if args.preview:
        if args.subject not in subjects:
            print(f"Unknown subject '{args.subject}'. Known: {', '.join(subjects)}")
            return
        _run_preview(config, subjects[args.subject], args)


def _run_preview(config, subject, args):
    first = last = None
    if args.pages:
        try:
            first, last = (int(x) for x in args.pages.split("-"))
        except ValueError:
            print("Page range must look like: 140-146")
            return

    print(f"Extracting pages {first or 1}-{last or 'end'} of {args.preview}...")
    pages = extract_pages(args.preview, first, last)
    chunks = chunk_pages(pages)
    print(f"{len(pages)} pages -> {len(chunks)} chunk(s)")

    print(f"Generating {subject.name} cards with {LLMClient().provider}...")
    generator = CardGenerator(LLMClient(), config)
    cards, errors = generator.generate(subject, chunks, topic_hint=args.topic)

    valid, rejected = validate_cards(cards)

    # Duplicate check: batch + database + Anki (Anki layer skipped if closed).
    try:
        anki_client = AnkiConnectClient()
        anki_client.check_connection()
    except AnkiConnectionError:
        anki_client = None
    unique, duplicates = find_duplicates(valid, anki_client=anki_client,
                                         deck=subject.anki_deck)

    print()
    for index, card in enumerate(unique, start=1):
        print(f"[{index}] ({card.card_kind}) {card.front}")
        if card.back:
            print(f"     back: {card.back}")
        if card.extra:
            print(f"     extra: {card.extra}")
        print(f"     tags: {', '.join(card.tags)}")
    print()
    print(f"Summary: {len(cards)} generated -> {len(valid)} valid -> "
          f"{len(unique)} unique ({len(duplicates)} duplicates, "
          f"{len(rejected)} rejected)")
    if duplicates:
        print("Duplicates:")
        for card, reason in duplicates:
            print(f"  - {card.front[:60]}... [{reason}]")
    if rejected:
        print("Rejected:")
        for card, issues in rejected:
            print(f"  - {card.front[:60]}... [{'; '.join(issues)}]")
    if errors:
        print("Malformed from LLM:")
        for error in errors:
            print(f"  - {error}")
    print("\nThis was a PREVIEW — nothing was written to Anki.")


if __name__ == "__main__":
    main()
