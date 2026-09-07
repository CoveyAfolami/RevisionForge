"""AnkiConnect HTTP client (roadmap Phases 5–6).

Deterministic: every method maps to exactly one AnkiConnect action, and
all network + error handling lives here so nothing else in the app ever
touches raw HTTP.
"""

import os

import requests

from ..observability.errors import AnkiConnectionError

DEFAULT_URL = "http://localhost:8765"


class AnkiConnectClient:
    def __init__(self, url: str | None = None, key: str | None = None,
                 timeout: int = 10, transport=None):
        # Late .env loading: safe even if the app hasn't called load_dotenv yet.
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass

        self.url = url or os.getenv("ANKI_CONNECT_URL", DEFAULT_URL)
        self.key = key or os.getenv("ANKI_CONNECT_KEY")
        self.timeout = timeout
        # `transport` is injectable so tests can pass a fake AnkiConnect
        # instead of monkeypatching network calls.
        self._transport = transport or requests.post

    def _invoke(self, action: str, **params):
        request = {"action": action, "version": 6, "params": params}
        if self.key:
            request["key"] = self.key
        try:
            response = self._transport(self.url, json=request, timeout=self.timeout)
        except requests.exceptions.ConnectionError as error:
            raise AnkiConnectionError(
                f"Cannot reach AnkiConnect at {self.url} — is Anki running?"
            ) from error
        except requests.exceptions.Timeout as error:
            raise AnkiConnectionError("AnkiConnect timed out") from error

        if response.status_code != 200:
            raise AnkiConnectionError(
                f"AnkiConnect returned HTTP {response.status_code}"
            )
        data = response.json()
        if data.get("error") is not None:
            raise AnkiConnectionError(f"AnkiConnect error: {data['error']}")
        return data["result"]

    # ---- reads (safe operations) ----

    def check_connection(self) -> int:
        """Returns the AnkiConnect API version if reachable."""
        return self._invoke("version")

    def get_decks(self) -> list[str]:
        return self._invoke("deckNames")

    def get_note_types(self) -> list[str]:
        return self._invoke("modelNames")

    def get_note_type_fields(self, note_type: str) -> list[str]:
        return self._invoke("modelFieldNames", modelName=note_type)

    def find_notes(self, query: str) -> list[int]:
        """AnkiConnect search query, e.g. 'deck:"GCSE::Chemistry" isotope'."""
        return self._invoke("findNotes", query=query)

    def get_notes_info(self, note_ids: list[int]) -> list[dict]:
        return self._invoke("notesInfo", notes=note_ids)

    # ---- writes (require user approval upstream) ----

    def create_deck(self, deck_name: str) -> int:
        return self._invoke("createDeck", deck=deck_name)

    def add_notes(self, notes: list[dict]) -> list[int | None]:
        """Returns one note id per note; None means Anki declined it
        (usually a duplicate — we deliberately don't allow those)."""
        return self._invoke("addNotes", notes=notes)

    def add_note(self, note: dict) -> int:
        results = self.add_notes([note])
        if not results or results[0] is None:
            raise AnkiConnectionError(
                "Anki declined to add the note (duplicate or invalid fields)"
            )
        return results[0]

    def update_note_fields(self, note_id: int, fields: dict[str, str]) -> None:
        self._invoke("updateNoteFields", note={"id": note_id, "fields": fields})

    def delete_notes(self, note_ids: list[int]) -> None:
        self._invoke("deleteNotes", notes=note_ids)
