"""An in-memory stand-in for AnkiConnect, used by unit tests.

No network, no real Anki — implements just enough AnkiConnect behaviour
(decks, note types, findNotes, addNotes with duplicate rejection,
notesInfo, updateNoteFields, deleteNotes) to test the client, mapper,
and verifier end to end.
"""

import re


class FakeAnkiConnect:
    def __init__(self, decks=None, models=None):
        self.decks = set(decks or [])
        self.models = dict(models or {})  # {note_type_name: [field names]}
        self.notes = {}  # note_id -> {deckName, modelName, fields, tags}
        self._next_id = 1
        self.requests = []

    def __call__(self, url, json=None, timeout=None):
        self.requests.append(json)
        action = json["action"]
        params = json.get("params", {})
        result, error = self._dispatch(action, params)
        return _Response(result, error)

    def _dispatch(self, action, params):
        if action == "version":
            return 6, None
        if action == "deckNames":
            return sorted(self.decks), None
        if action == "modelNames":
            return sorted(self.models), None
        if action == "modelFieldNames":
            name = params["modelName"]
            if name not in self.models:
                return None, f"model was not found: {name}"
            return self.models[name], None
        if action == "createDeck":
            self.decks.add(params["deck"])
            return len(self.decks), None
        if action == "findNotes":
            matches = [nid for nid in sorted(self.notes)
                       if self._query_matches(params["query"], self.notes[nid])]
            return matches, None
        if action == "addNotes":
            results = []
            for note in params["notes"]:
                results.append(self._try_add(note))
            return results, None
        if action == "notesInfo":
            out = []
            for nid in params["notes"]:
                note = self.notes.get(nid)
                if note is None:
                    continue
                out.append({
                    "noteId": nid,
                    "modelName": note["modelName"],
                    "fields": {name: {"value": value, "order": i}
                               for i, (name, value) in enumerate(note["fields"].items())},
                    "tags": note["tags"],
                    "cards": [{"deckName": note["deckName"]}],
                })
            return out, None
        if action == "updateNoteFields":
            note = self.notes[params["note"]["id"]]
            note["fields"].update(params["note"]["fields"])
            return None, None
        if action == "deleteNotes":
            for nid in params["notes"]:
                self.notes.pop(nid, None)
            return None, None
        return None, f"unsupported action: {action}"

    def _try_add(self, note):
        model = self.models.get(note["modelName"])
        if model is None:
            return None
        flat = " ".join(note["fields"].get(f, "") for f in model)
        allow_dup = note.get("options", {}).get("allowDuplicate", False)
        for existing in self.notes.values():
            existing_flat = " ".join(existing["fields"].get(f, "") for f in model)
            if existing["modelName"] == note["modelName"] and existing_flat == flat \
                    and not allow_dup:
                return None  # duplicate rejected, like real AnkiConnect
        note_id = self._next_id
        self._next_id += 1
        self.notes[note_id] = {
            "deckName": note["deckName"],
            "modelName": note["modelName"],
            "fields": dict(note["fields"]),
            "tags": list(note.get("tags", [])),
        }
        return note_id

    @staticmethod
    def _query_matches(query, note):
        deck_terms = re.findall(r'deck:"([^"]+)"', query)
        rest = re.sub(r'deck:"[^"]+"', "", query)
        phrases = re.findall(r'"([^"]+)"', rest)
        plain_terms = [t for t in re.sub(r'"[^"]+"', "", rest).split() if t]
        if any(note["deckName"] != d for d in deck_terms):
            return False
        text = " ".join(note["fields"].values()).lower()
        phrases_ok = all(p.lower() in text for p in phrases)
        terms_ok = all(t.lower() in text for t in plain_terms)
        return phrases_ok and terms_ok


class _Response:
    def __init__(self, result, error, status_code=200):
        self._result = result
        self._error = error
        self.status_code = status_code

    def json(self):
        return {"result": self._result, "error": self._error}
