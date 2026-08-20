from .lifecycle import Application
from ..anki import anki_connect as ac

#A simple test script to check if the AnkiConnect API is working correctly. It retrieves the names of all decks in Anki and prints them to the console.
def main():
    print("Hello. Revision!")
    app = Application(name="RevisionForge")
    app.start()

    deck_names = ac.get_deck_names()
    model_names = ac.get_model_names()
    
    # for deck_name in deck_names:
    #    print(deck_name)
    

    for model_name in model_names:
        print(model_name)

    request = ac.build_deck_names_request()
    #print("Request:", request)

    response = ac.send_request(request)
    #print(response)

if __name__ == "__main__":
    main()