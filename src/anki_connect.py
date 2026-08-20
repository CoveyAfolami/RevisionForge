import requests
from dotenv import load_dotenv
import os

load_dotenv()

anki_api_key = os.getenv("anki_api_key")

def handle_response(response):
    if response["error"] is not None:
        raise Exception(f"AnkiConnect error: {response['error']}")
    
    return response["result"]

#Builds a request to get the names of all decks in Anki
def build_deck_names_request():
    return {
        "action": "deckNames",
        "version": 6,
        "params": {},
        "key": anki_api_key 
    }

# Retrieves the names of all decks in Anki
def get_deck_names():
    request = build_deck_names_request()
    response = send_request(request)
    return handle_response(response)

#Builds a request to get the names of all models in Anki
def build_model_names_request():
    return {
        "action": "modelNames",
        "version": 6,
        "params": {},
        "key": anki_api_key 
    }

# Retrieves the names of all models in Anki
def get_model_names():
    request = build_model_names_request()
    response = send_request(request)
    return handle_response(response)

def send_request(request):

    response = requests.post(
        "http://localhost:8765",
         json=request,
         timeout=10,
    )

    return response.json()