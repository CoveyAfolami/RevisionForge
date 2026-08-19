import requests
from dotenv import load_dotenv
import os

load_dotenv()

anki_api_key = os.getenv("anki_api_key")

def get_deck_names():
    request = build_deck_names_request()
    response = send_request(request)
    return response.get("result", [])

def build_deck_names_request():
    return {
        "action": "deckNames",
        "version": 6,
        "params": {},
        "key": anki_api_key 
    }

def send_request(request):

    response = requests.post(
        "http://localhost:8765",
         json=request,
         timeout=10,
    )

    return response.json()