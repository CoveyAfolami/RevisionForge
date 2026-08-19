from anki_connect import AnkiConnectError, get_deck_names


def main() -> None:
    """List available Anki decks to confirm the local connection works."""
    try:
        deck_names = get_deck_names()
    except AnkiConnectError as error:
        print(error)
        return

    print("Connected to AnkiConnect. Available decks:")
    for deck_name in deck_names:
        print(f"- {deck_name}")


if __name__ == "__main__":
    main()
