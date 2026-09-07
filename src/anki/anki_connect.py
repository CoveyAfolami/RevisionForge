"""Backwards-compatible module-level functions.

New code should use AnkiConnectClient directly (src.anki.client).
This shim keeps existing scripts working.
"""

import requests

from ..observability.errors import AnkiConnectionError
from .client import AnkiConnectClient

_default = AnkiConnectClient()


def get_deck_names() -> list[str]:
    return _default.get_decks()


def get_model_names() -> list[str]:
    return _default.get_note_types()


def build_deck_names_request() -> dict:
    request = {"action": "deckNames", "version": 6, "params": {}}
    if _default.key:
        request["key"] = _default.key
    return request


def build_model_names_request() -> dict:
    request = {"action": "modelNames", "version": 6, "params": {}}
    if _default.key:
        request["key"] = _default.key
    return request


def send_request(request: dict) -> dict:
    """Legacy raw request sender — returns the full response envelope."""
    try:
        response = requests.post(_default.url, json=request, timeout=_default.timeout)
    except requests.exceptions.ConnectionError as error:
        raise AnkiConnectionError(
            f"Cannot reach AnkiConnect at {_default.url} — is Anki running?"
        ) from error
    return response.json()
