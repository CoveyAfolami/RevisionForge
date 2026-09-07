"""RevisionForge command-line entry point.

Usage:
    python -m src.app.main --anki-check          # connection + decks + note types
    python -m src.app.main --fields Cloze        # real fields of a note type
    python -m src.app.main --map chemistry       # where cards go for a subject
"""

import argparse

from ..anki.client import AnkiConnectClient
from ..anki.mapper import AnkiMapper
from ..config.loader import load_config
from ..observability.logging import configure_logging


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
    args = parser.parse_args(argv)

    config = load_config()
    configure_logging(config.settings.log_level, config.settings.log_file)

    if not any(vars(args).values()):
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
        subjects = {s.name: s for s in config.subjects}
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


if __name__ == "__main__":
    main()
