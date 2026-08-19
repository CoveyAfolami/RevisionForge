"""Small client for AnkiConnect's local HTTP API."""

import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ANKI_CONNECT_URL = "http://127.0.0.1:8765"
ANKI_CONNECT_VERSION = 6
ANKI_CONNECT_API_KEY_ENVIRONMENT_VARIABLE = "ANKI_CONNECT_API_KEY"


class AnkiConnectError(RuntimeError):
    """Raised when AnkiConnect cannot complete a request."""


def invoke(action: str, **params: Any) -> Any:
    """Call one AnkiConnect action and return its result.

    AnkiConnect returns a JSON object with a ``result`` or an ``error``.
    This function turns transport and API errors into one clear exception type.
    """
    try:
        request_payload = {
            "action": action,
            "version": ANKI_CONNECT_VERSION,
            "params": params,
        }
        api_key = os.getenv(ANKI_CONNECT_API_KEY_ENVIRONMENT_VARIABLE)
        if api_key:
            request_payload["key"] = api_key

        request = Request(
            ANKI_CONNECT_URL,
            data=json.dumps(request_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, ValueError) as error:
        raise AnkiConnectError(
            "Could not reach AnkiConnect. Open Anki and confirm the "
            "AnkiConnect add-on is enabled."
        ) from error

    if not isinstance(payload, dict):
        raise AnkiConnectError("AnkiConnect returned an invalid response.")

    if payload.get("error") is not None:
        if payload["error"] == "valid api key must be provided":
            raise AnkiConnectError(
                f"AnkiConnect requires an API key. Set the "
                f"{ANKI_CONNECT_API_KEY_ENVIRONMENT_VARIABLE} environment variable "
                "before running the program."
            )
        raise AnkiConnectError(f"AnkiConnect error: {payload['error']}")

    return payload.get("result")


def get_deck_names() -> list[str]:
    """Return the current Anki deck names (a read-only operation)."""
    return invoke("deckNames")
